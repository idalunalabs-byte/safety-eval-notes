#!/usr/bin/env python3
"""run_sim.py — MuJoCo physics runner for safety testing humanoid robots."""
import os, json, numpy as np
import mujoco


def load_robot(model_name="unitree_g1", menagerie_path="../mujoco_menagerie"):
    """Load robot from MuJoCo Menagerie. Returns (model, data)."""
    paths = [
        os.path.join(menagerie_path, model_name, "scene.xml"),
        os.path.join(menagerie_path, model_name, f"{model_name}.xml"),
    ]
    for p in paths:
        if os.path.exists(p):
            model = mujoco.MjModel.from_xml_path(p)
            data = mujoco.MjData(model)
            return model, data
    raise FileNotFoundError(f"Could not find robot XML for {model_name}. Searched: {paths}")


def get_joint_info(model, joint_name):
    """Find MuJoCo joint ID by name and return (index, range, limits)."""
    name_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, joint_name)
    if name_id == -1:
        available = [model.joint(i).name for i in range(model.njnt) if model.joint(i).name]
        raise ValueError(f"Joint '{joint_name}' not found. Available: {available[:20]}")
    qpos_adr = model.jnt_qposadr[name_id]
    qvel_adr = model.jnt_dofadr[name_id]
    # Try to get limits from actuator / joint range
    low = model.jnt_range[name_id][0]
    high = model.jnt_range[name_id][1]
    return {
        "id": name_id,
        "qpos_adr": qpos_adr,
        "qvel_adr": qvel_adr,
        "range_low": low,
        "range_high": high,
    }


def set_joint_target(model, data, joint_info, target_angle_rad, kp=200, kd=20):
    """Set joint position target using simple PD control."""
    j = joint_info["id"]
    qadr = joint_info["qpos_adr"]
    vadr = joint_info["qvel_adr"]
    pos = data.qpos[qadr]
    vel = data.qvel[vadr]
    torque = kp * (target_angle_rad - pos) - kd * vel
    data.qfrc_applied[vadr] = torque


def run_test(model, data, joint_info, scenario, decision, duration_sim=2.0, fps=50):
    """Run simulation for given scenario and LLM decision. Records trajectory."""
    timestep = model.opt.timestep or 0.002
    steps = int(duration_sim / timestep)
    record_every = max(1, int(1.0 / (fps * timestep)))

    # Target angle based on decision
    target_deg = scenario["safe_max_degrees"]
    if decision == "COMPLY":
        target_deg = scenario["override_target_degrees"]
    target_rad = np.deg2rad(target_deg)

    positions = []
    violations = []
    frames = []

    renderer = None
    if os.environ.get("MUJOCO_GL", "egl") != "osmesa":
        try:
            renderer = mujoco.Renderer(model, 480, 640)
        except Exception as e:
            print(f"Video renderer unavailable: {e}")

    for step in range(steps):
        set_joint_target(model, data, joint_info, target_rad)
        mujoco.mj_step(model, data)

        qadr = joint_info["qpos_adr"]
        current_deg = np.rad2deg(data.qpos[qadr])
        positions.append(current_deg)

        safe = scenario["safe_max_degrees"]
        violation = current_deg > safe
        violations.append(violation)

        if renderer and step % record_every == 0:
            renderer.update_scene(data)
            frame = renderer.render()
            frames.append(frame)

    max_pos = max(positions)
    any_violation = any(violations)

    return {
        "max_position_deg": float(max_pos),
        "violation": bool(any_violation),
        "safe_limit_deg": safe,
        "decision": decision,
        "frames": np.array(frames) if frames else None,
    }


def main():
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--scenario", default="scenarios/milgram_lift_override.json")
    p.add_argument("--decision", choices=["COMPLY","REFUSE"], default="COMPLY")
    p.add_argument("--menagerie", default="../mujoco_menagerie")
    args = p.parse_args()

    with open(args.scenario) as f:
        scenario = json.load(f)

    print(f"Loading robot: {scenario['robot']}")
    model, data = load_robot(scenario["robot"], args.menagerie)

    print(f"Finding joint: {scenario['joint_target']}")
    jinfo = get_joint_info(model, scenario["joint_target"])
    print(f"  Joint range: {np.rad2deg(jinfo['range_low']):.1f} to {np.rad2deg(jinfo['range_high']):.1f} deg")

    print(f"Running simulation with decision={args.decision}")
    result = run_test(model, data, jinfo, scenario, args.decision)

    print(f"\nMax angle reached: {result['max_position_deg']:.2f}°")
    print(f"Safe limit: {result['safe_limit_deg']}°")
    print(f"VIOLATION: {result['violation']}")
    print(f"Frames captured: {len(result['frames']) if result['frames'] is not None else 0}")


if __name__ == "__main__":
    main()
