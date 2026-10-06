#!/usr/bin/env python3
"""
Generate a low-poly cab-over box truck for Source (HL2) as a starting point.
Writes: truck_ref.smd, truck_phys.smd, truck.qc, two .vmt files.
Everything is original geometry (boxes + cylinders): no ETS2 or Valve assets.

Usage:  python make_truck.py [--out build] [--forward x|y] [--flip-winding]
Units are Source units (1 unit ~ 1 inch). Truck is ~280 long, ~90 wide.
"""
import argparse, math, os

def box(x0, x1, y0, y1, z0, z1):
    """12 triangles, each ((pos),(normal),(u,v)) x3. CCW seen from outside."""
    f = []
    def quad(a, b, c, d, n):
        f.append([(a, n, (0, 0)), (b, n, (1, 0)), (c, n, (1, 1))])
        f.append([(a, n, (0, 0)), (c, n, (1, 1)), (d, n, (0, 1))])
    quad((x1,y0,z0),(x1,y1,z0),(x1,y1,z1),(x1,y0,z1),(1,0,0))     # +x front
    quad((x0,y1,z0),(x0,y0,z0),(x0,y0,z1),(x0,y1,z1),(-1,0,0))    # -x rear
    quad((x1,y1,z0),(x0,y1,z0),(x0,y1,z1),(x1,y1,z1),(0,1,0))     # +y left
    quad((x0,y0,z0),(x1,y0,z0),(x1,y0,z1),(x0,y0,z1),(0,-1,0))    # -y right
    quad((x0,y0,z1),(x1,y0,z1),(x1,y1,z1),(x0,y1,z1),(0,0,1))     # top
    quad((x0,y1,z0),(x1,y1,z0),(x1,y0,z0),(x0,y0,z0),(0,0,-1))    # bottom
    return f

def wheel(cx, cy, cz, r, hw, n=12):
    """Cylinder with its axis along Y."""
    f = []
    for i in range(n):
        a0, a1 = 2*math.pi*i/n, 2*math.pi*(i+1)/n
        p = lambda a, y: (cx + r*math.cos(a), cy + y, cz + r*math.sin(a))
        nm = lambda a: (math.cos(a), 0, math.sin(a))
        u0, u1 = i/n, (i+1)/n
        f.append([(p(a0,-hw), nm(a0), (u0,0)), (p(a1,-hw), nm(a1), (u1,0)), (p(a1,hw), nm(a1), (u1,1))])
        f.append([(p(a0,-hw), nm(a0), (u0,0)), (p(a1,hw), nm(a1), (u1,1)), (p(a0,hw), nm(a0), (u0,1))])
        for y, ny, order in ((hw, 1, (0, 1)), (-hw, -1, (1, 0))):
            c = (cx, cy + y, cz)
            aa = (a0, a1)[order[0]]; bb = (a0, a1)[order[1]]
            f.append([(c,(0,ny,0),(.5,.5)), (p(aa,y),(0,ny,0),(.5,.5)), (p(bb,y),(0,ny,0),(.5,.5))])
    return f

# --- layout (x forward, y left, z up; cab-over: cab sits ON the front axle) ---
FRONT_X, REAR_X, WHEEL_R, TRACK = 100.0, -90.0, 22.0, 38.0
CHASSIS = (-140, 140, -34, 34, 30, 42)
CAB     = (50, 140, -42, 42, 42, 135)       # flat-nosed cab
BOX     = (-140, 42, -45, 45, 46, 150)      # simple white box body
STEER   = (112, 118, -7, 7, 92, 98)         # placeholder steering wheel

BONES = [("root", -1, (0, 0, 0))]
WHEELS = {}
for tag, x, y in (("fl", FRONT_X, TRACK), ("fr", FRONT_X, -TRACK),
                  ("rl", REAR_X, TRACK), ("rr", REAR_X, -TRACK)):
    h = len(BONES); BONES.append((f"vehicle_wheel_{tag}_height", 0, (x, y, WHEEL_R)))
    s = len(BONES); BONES.append((f"vehicle_wheel_{tag}_spin", h, (0, 0, 0)))
    WHEELS[tag] = (s, (x, y, WHEEL_R))
steer_bone = len(BONES); BONES.append(("vehicle_steer", 0, (115, 0, 95)))

def build(flip):
    parts = [  # (material, bone, triangles)
        ("c17_truck_cab", 0, box(*CHASSIS)), ("c17_truck_cab", 0, box(*CAB)),
        ("c17_truck_box", 0, box(*BOX)), ("c17_truck_cab", steer_bone, box(*STEER)),
    ]
    for tag, (bone, (x, y, z)) in WHEELS.items():
        parts.append(("c17_truck_cab", bone, wheel(x, y, z, WHEEL_R, 8)))
    return parts

def xform(p, forward):
    x, y, z = p
    return (x, y, z) if forward == "x" else (-y, x, z)   # rotate 90 deg about Z

def write_smd(path, parts, forward, flip, bones_all=True):
    with open(path, "w") as o:
        o.write("version 1\nnodes\n")
        for i, (n, par, _) in enumerate(BONES):
            o.write(f'{i} "{n}" {par}\n')
        o.write("end\nskeleton\ntime 0\n")
        for i, (n, par, pos) in enumerate(BONES):
            x, y, z = xform(pos, forward)
            o.write(f"{i} {x:.4f} {y:.4f} {z:.4f} 0 0 0\n")
        o.write("end\ntriangles\n")
        for mat, bone, tris in parts:
            for t in tris:
                if flip: t = [t[0], t[2], t[1]]
                o.write(mat + "\n")
                for pos, nrm, uv in t:
                    px, py, pz = xform(pos, forward); nx, ny, nz = xform(nrm, forward)
                    o.write(f"{bone} {px:.4f} {py:.4f} {pz:.4f} {nx:.4f} {ny:.4f} {nz:.4f} {uv[0]:.4f} {uv[1]:.4f}\n")
        o.write("end\n")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="build")
    ap.add_argument("--forward", choices=["x", "y"], default="x",
                    help="model forward axis; check against Valve's vehicle docs and flip if the truck drives sideways")
    ap.add_argument("--flip-winding", action="store_true", help="use if faces look inside-out in HLMV")
    a = ap.parse_args()
    os.makedirs(os.path.join(a.out, "modelsrc"), exist_ok=True)
    mats = os.path.join(a.out, "materials", "models", "c17_freight"); os.makedirs(mats, exist_ok=True)

    parts = build(a.flip_winding)
    write_smd(os.path.join(a.out, "modelsrc", "truck_ref.smd"), parts, a.forward, a.flip_winding)
    # collision: three boxes, all on root (compile with $concave)
    phys = [("phys", 0, box(*CHASSIS) + box(*CAB) + box(*BOX))]
    write_smd(os.path.join(a.out, "modelsrc", "truck_phys.smd"), phys, a.forward, a.flip_winding)

    eye = xform((118, 18, 112), a.forward)
    qc = f'''// City 17 Freight truck - DRAFT. Compare every vehicle-specific line with Valve's
// vehicle QC documentation (VDC "Vehicle" pages) before trusting it.
$modelname "c17_freight/truck.mdl"
$body "truck" "truck_ref.smd"
$cdmaterials "models/c17_freight/"
$surfaceprop "metal"
$mostlyopaque

$sequence idle "truck_ref" loop fps 1

$attachment "vehicle_driver_eyes" "root" {eye[0]:.1f} {eye[1]:.1f} {eye[2]:.1f} rotate 0 0 0

$collisionmodel "truck_phys.smd" {{
    $mass 4000
    $concave
    $maxconvexpieces 3
    $damping 0
    $rotdamping 0
}}
// TODO (needs HLMV testing): vehicle script keyvalues, wheel $jointconstrain / bone
// setup, extra attachments (passenger, exhaust, headlights). The bone names here are
// a best guess at Valve's convention; verify against the docs.
'''
    open(os.path.join(a.out, "modelsrc", "truck.qc"), "w").write(qc)
    for name, col in (("c17_truck_cab", "[0.75 0.78 0.80]"), ("c17_truck_box", "[0.95 0.95 0.95]")):
        open(os.path.join(mats, name + ".vmt"), "w").write(
            f'"VertexLitGeneric"\n{{\n\t"$basetexture" "dev/reflectivity_100"\n\t"$color" "{col}"\n\t"$surfaceprop" "metal"\n}}\n')
    tris = sum(len(t) for _, _, t in parts)
    print(f"wrote {tris} triangles, {len(BONES)} bones -> {a.out}/")

if __name__ == "__main__":
    main()
