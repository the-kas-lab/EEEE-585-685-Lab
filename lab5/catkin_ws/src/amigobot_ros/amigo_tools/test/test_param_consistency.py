#!/usr/bin/env python3
"""
test_param_consistency.py
=========================
Guards the "single source of truth" claim at the top of
amigo_description/config/amigo_params.yaml.

Nothing in ROS enforces that the YAML and the URDF agree.  The URDF cannot read
YAML, so every physical constant is written down at least twice, and the sonar
mounting poses are written down four times:

    1. amigo_description/config/amigo_params.yaml   <- the source of truth
    2. amigo_description/urdf/amigo_sonar.xacro     (what Gazebo simulates)
    3. amigo_tools/scripts/sonar_aggregator.py      (DEFAULT_POSES fallback)
    4. amigo_tools/scripts/sonar_splitter.py        (DEFAULT_POSES fallback)

If (1) and (2) drift apart, the simulated transducers are not where the node
computing echo positions thinks they are, and the sonar quietly reports points
in the wrong place -- no error, no warning, just wrong data.  The same is true
of wheel_separation, which sets both the Gazebo diff-drive plugin's kinematics
and the dead reckoning students are asked to compare against it.

wheel_separation is flagged VERIFY in the YAML -- an estimate awaiting
calibration on the real robot -- so this drift is not hypothetical: somebody
is going to edit it.  This test makes sure they edit all the copies.

What is checked
---------------
A. Scalars in the YAML vs. <xacro:property> in amigo_properties.xacro.
B. YAML sonar_poses vs. the sonar_N_joint origins in the robot description.
C. YAML wheel geometry vs. the wheel and base_footprint joint origins.
D. YAML values vs. the hardcoded fallbacks in the Python nodes, both the
   DEFAULT_POSES lists and every rospy.get_param("~key", <default>) whose key
   appears in the YAML.

amigo_student/scripts is deliberately excluded from (D): those files hardcode
constants on purpose, as the TODOs the students replace.

Running it
----------
    python3 $(rospack find amigo_tools)/test/test_param_consistency.py
    catkin_make run_tests_amigo_tools                # as part of the build

It needs no ROS master, no Gazebo and no hardware, so it is the cheapest check
in the TA checklist -- run it first.

Checks B and C use the real xacro expansion when xacro and the ROS package path
are available, which is the honest test -- it evaluates the ${...} expressions
exactly as Gazebo and RViz will.  Off a ROS machine it falls back to reading the
literal <xacro:sonar_unit> call sites, which covers the sonar poses but not the
computed joint origins; check C is skipped in that mode.  The mode in use is
printed at the top of the run.
"""

import ast
import math
import os
import sys
import unittest
import xml.etree.ElementTree as ET

import yaml

XACRO_NS = "{http://www.ros.org/wiki/xacro}"

# Tolerance for comparing two hand-typed decimal literals.  Tight enough that a
# real edit to one copy fails, loose enough that 0.02 and 0.020 agree.
TOL = 1e-6

# YAML key -> xacro property name, where the two spell the same quantity
# differently.  Keys not listed here are compared under their own name.
PROPERTY_ALIASES = {
    "min_range": "sonar_min_range",
    "max_range": "sonar_max_range",
    "fov": "sonar_fov",
}

# YAML scalars that must appear in the URDF.  Everything else in the YAML
# (encoder counts, velocity limits) is used only by the Python nodes and has no
# URDF counterpart, so it is covered by check D alone.
SHARED_SCALARS = [
    "wheel_radius",
    "wheel_separation",
    "min_range",
    "max_range",
    "fov",
]

# Directories whose *.py fallbacks must match the YAML.  amigo_student is
# excluded on purpose -- see the module docstring.
SCRIPT_DIRS = [
    os.path.join("amigo_tools", "scripts"),
    "solutions",
]


# --------------------------------------------------------------------------
# locating the packages
# --------------------------------------------------------------------------

def find_workspace_root():
    """Directory holding amigo_description/, however this test was started."""
    try:
        import rospkg
        share = rospkg.RosPack().get_path("amigo_description")
        # Installed layout puts the package under share/; the source layout has
        # it directly under amigobot_ros/.  Either way the parent is the root.
        root = os.path.dirname(share)
        if os.path.isfile(_params_path(root)):
            return root
    except Exception:
        pass

    here = os.path.abspath(os.path.dirname(__file__))
    while True:
        if os.path.isfile(_params_path(here)):
            return here
        parent = os.path.dirname(here)
        if parent == here:
            raise RuntimeError(
                "cannot find amigo_description/config/amigo_params.yaml above %s"
                % os.path.dirname(__file__))
        here = parent


def _params_path(root):
    return os.path.join(root, "amigo_description", "config", "amigo_params.yaml")


ROOT = find_workspace_root()
URDF_DIR = os.path.join(ROOT, "amigo_description", "urdf")


# --------------------------------------------------------------------------
# readers
# --------------------------------------------------------------------------

def load_yaml_params():
    with open(_params_path(ROOT)) as fh:
        return yaml.safe_load(fh)


def load_xacro_properties():
    """{name: raw value string} for every <xacro:property> in the properties file."""
    tree = ET.parse(os.path.join(URDF_DIR, "amigo_properties.xacro"))
    return {el.get("name"): el.get("value")
            for el in tree.getroot().iter(XACRO_NS + "property")
            if el.get("name") is not None}


def expand_urdf():
    """
    Full xacro expansion of amigo.urdf.xacro, or None if xacro is unavailable.

    simulation:=false keeps Gazebo's plugin block out of the way; it changes
    nothing about the geometry being checked here.
    """
    try:
        import xacro
        doc = xacro.process_file(
            os.path.join(URDF_DIR, "amigo.urdf.xacro"),
            mappings={"simulation": "false"})
        return ET.fromstring(doc.toxml())
    except Exception as exc:                     # no xacro, or $(find) failed
        print("  note: xacro expansion unavailable (%s: %s)"
              % (type(exc).__name__, exc))
        return None


def poses_from_expanded(urdf):
    """{id: (x, y, z, yaw)} read from the sonar_N_joint origins of a real URDF."""
    poses = {}
    for joint in urdf.iter("joint"):
        name = joint.get("name") or ""
        if not (name.startswith("sonar_") and name.endswith("_joint")):
            continue
        sid = int(name[len("sonar_"):-len("_joint")])
        origin = joint.find("origin")
        x, y, z = (float(v) for v in origin.get("xyz").split())
        yaw = float(origin.get("rpy").split()[2])
        poses[sid] = (x, y, z, yaw)
    return poses


def poses_from_call_sites(properties):
    """
    {id: (x, y, z, yaw)} read from the literal <xacro:sonar_unit .../> calls.

    Fallback for machines without xacro.  The call sites carry x, y and yaw as
    plain decimals; z comes from the sonar_z property, which is likewise a
    plain decimal.
    """
    tree = ET.parse(os.path.join(URDF_DIR, "amigo_sonar.xacro"))
    z = float(properties["sonar_z"])
    poses = {}
    for el in tree.getroot().iter(XACRO_NS + "sonar_unit"):
        poses[int(el.get("id"))] = (float(el.get("x")), float(el.get("y")),
                                    z, float(el.get("yaw")))
    return poses


def joint_origin(urdf, joint_name):
    for joint in urdf.iter("joint"):
        if joint.get("name") == joint_name:
            return [float(v) for v in joint.find("origin").get("xyz").split()]
    return None


def scan_script_defaults(path):
    """
    Hardcoded fallbacks in one Python node.

    Returns (default_poses, {param_name: default_value}) where default_poses is
    the DEFAULT_POSES module constant if present, and the dict holds every
    rospy.get_param("~name", <literal>) found in the file.
    """
    with open(path) as fh:
        tree = ast.parse(fh.read(), filename=path)

    default_poses = None
    params = {}

    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "DEFAULT_POSES":
                    default_poses = ast.literal_eval(node.value)

        if (isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr == "get_param"
                and len(node.args) == 2):
            try:
                key = ast.literal_eval(node.args[0])
                value = ast.literal_eval(node.args[1])
            except ValueError:
                continue                          # non-literal default; skip
            if isinstance(key, str) and key.startswith("~"):
                params[key[1:]] = value

    return default_poses, params


def iter_scripts():
    for rel in SCRIPT_DIRS:
        directory = os.path.join(ROOT, rel)
        if not os.path.isdir(directory):
            continue                              # solutions/ is deleted at release
        for name in sorted(os.listdir(directory)):
            if name.endswith(".py"):
                yield os.path.join(rel, name), os.path.join(directory, name)


def close(a, b):
    return abs(float(a) - float(b)) <= TOL


def _scalar(value):
    """True for values a YAML key and a Python default can be compared as."""
    return isinstance(value, (int, float, str)) and not isinstance(value, bool)


# --------------------------------------------------------------------------
# the tests
# --------------------------------------------------------------------------

class ParamConsistency(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        print("\nchecking parameter consistency under %s" % ROOT)
        cls.params = load_yaml_params()
        cls.properties = load_xacro_properties()
        cls.urdf = expand_urdf()
        if cls.urdf is not None:
            cls.urdf_poses = poses_from_expanded(cls.urdf)
            print("  mode: full xacro expansion")
        else:
            cls.urdf_poses = poses_from_call_sites(cls.properties)
            print("  mode: literal xacro call sites "
                  "(computed joint origins not checked)")

    # -- A ------------------------------------------------------------------
    def test_scalars_match_xacro_properties(self):
        bad = []
        for key in SHARED_SCALARS:
            prop = PROPERTY_ALIASES.get(key, key)
            self.assertIn(key, self.params,
                          "amigo_params.yaml is missing '%s'" % key)
            self.assertIn(prop, self.properties,
                          "amigo_properties.xacro is missing property '%s'" % prop)
            if not close(self.params[key], self.properties[prop]):
                bad.append("  %-18s yaml=%-10s xacro %s=%s"
                           % (key, self.params[key], prop, self.properties[prop]))
        self.assertFalse(bad, "YAML and amigo_properties.xacro disagree:\n"
                              + "\n".join(bad)
                              + "\n(edit both, they are kept in sync by hand)")

    # -- B ------------------------------------------------------------------
    def test_sonar_poses_match_urdf(self):
        yaml_poses = {int(p["id"]): p for p in self.params["sonar_poses"]}
        self.assertEqual(
            sorted(yaml_poses), sorted(self.urdf_poses),
            "transducer ids differ: yaml=%s urdf=%s"
            % (sorted(yaml_poses), sorted(self.urdf_poses)))

        bad = []
        for sid in sorted(yaml_poses):
            want = yaml_poses[sid]
            x, y, z, yaw = self.urdf_poses[sid]
            for field, got in (("x", x), ("y", y), ("z", z), ("yaw", yaw)):
                if not close(want[field], got):
                    bad.append("  sonar_%d.%-3s yaml=%-9s urdf=%s"
                               % (sid, field, want[field], got))
        self.assertFalse(
            bad,
            "sonar poses disagree between amigo_params.yaml and "
            "amigo_sonar.xacro:\n" + "\n".join(bad)
            + "\n(the poses come from ARIA's amigo-sh.p -- if you edit one "
              "copy, edit them all)")

    def test_sonar_frame_names_match_yaml_convention(self):
        """The prefix/suffix the nodes build frame names from must name real links."""
        if self.urdf is None:
            self.skipTest("needs the expanded URDF")
        links = {link.get("name") for link in self.urdf.iter("link")}
        prefix = self.params["frame_prefix"]
        suffix = self.params["frame_suffix"]
        missing = ["%s%d%s" % (prefix, int(p["id"]), suffix)
                   for p in self.params["sonar_poses"]
                   if "%s%d%s" % (prefix, int(p["id"]), suffix) not in links]
        self.assertFalse(
            missing,
            "frame_prefix/frame_suffix in amigo_params.yaml name links that do "
            "not exist in the URDF: %s\n(sonar_splitter.py stamps these into "
            "its Range headers; TF lookups on them would fail)" % missing)

    # -- C ------------------------------------------------------------------
    def test_wheel_geometry_matches_urdf(self):
        if self.urdf is None:
            self.skipTest("computed joint origins need the expanded URDF")

        half = float(self.params["wheel_separation"]) / 2.0
        for joint, expected_y in (("left_wheel_joint", half),
                                  ("right_wheel_joint", -half)):
            origin = joint_origin(self.urdf, joint)
            self.assertIsNotNone(origin, "URDF has no %s" % joint)
            self.assertTrue(
                close(origin[1], expected_y),
                "%s sits at y=%s, but wheel_separation=%s implies y=%s"
                % (joint, origin[1], self.params["wheel_separation"], expected_y))

        # base_footprint is base_link dropped by one wheel radius onto the
        # ground; if it disagrees the robot renders sunk into or floating above
        # the floor and every ground-truth comparison picks up a z offset.
        origin = joint_origin(self.urdf, "base_footprint_joint")
        self.assertIsNotNone(origin, "URDF has no base_footprint_joint")
        self.assertTrue(
            close(origin[2], -float(self.params["wheel_radius"])),
            "base_footprint_joint sits at z=%s, but wheel_radius=%s implies %s"
            % (origin[2], self.params["wheel_radius"],
               -float(self.params["wheel_radius"])))

    # -- D ------------------------------------------------------------------
    def test_script_default_poses_match_yaml(self):
        yaml_poses = {int(p["id"]): p for p in self.params["sonar_poses"]}
        bad = []
        for rel, path in iter_scripts():
            poses, _ = scan_script_defaults(path)
            if poses is None:
                continue
            got = {int(p["id"]): p for p in poses}
            if sorted(got) != sorted(yaml_poses):
                bad.append("  %s: DEFAULT_POSES has ids %s, yaml has %s"
                           % (rel, sorted(got), sorted(yaml_poses)))
                continue
            for sid in sorted(yaml_poses):
                for field in ("x", "y", "z", "yaw"):
                    if not close(yaml_poses[sid][field], got[sid][field]):
                        bad.append("  %s: sonar_%d.%-3s = %-9s yaml=%s"
                                   % (rel, sid, field, got[sid][field],
                                      yaml_poses[sid][field]))
        self.assertFalse(
            bad,
            "DEFAULT_POSES fallbacks have drifted from amigo_params.yaml:\n"
            + "\n".join(bad)
            + "\n(these are used whenever a node runs without the YAML loaded, "
              "e.g. plain rosrun)")

    def test_script_param_defaults_match_yaml(self):
        bad = []
        for rel, path in iter_scripts():
            _, defaults = scan_script_defaults(path)
            for key, value in sorted(defaults.items()):
                if key not in self.params:
                    continue                      # node-local param, no YAML twin
                want = self.params[key]
                if not _scalar(want) or not _scalar(value):
                    # e.g. get_param("~sonar_poses", []) -- a placeholder for a
                    # structured value, covered by the DEFAULT_POSES check.
                    continue
                if isinstance(want, str) or isinstance(value, str):
                    same = want == value
                else:
                    same = close(want, value)
                if not same:
                    bad.append("  %s: get_param('~%s', %r) but yaml has %r"
                               % (rel, key, value, want))
        self.assertFalse(
            bad,
            "hardcoded get_param fallbacks disagree with amigo_params.yaml:\n"
            + "\n".join(bad)
            + "\n(a node launched without the YAML would then behave "
              "differently from the same node inside amigo_interface.launch)")


if __name__ == "__main__":
    try:
        import rosunit
        rosunit.unitrun("amigo_tools", "test_param_consistency", ParamConsistency)
    except ImportError:
        sys.exit(0 if unittest.main(exit=False).result.wasSuccessful() else 1)
