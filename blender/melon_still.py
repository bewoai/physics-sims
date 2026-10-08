# Fizibilite testi: prosedürel karpuz, N düzlem kesimi, patlama anı, Cycles CPU render.
# blender -b -P melon_still.py -- <N> <out.png> <samples> <res_pct>
import bpy, bmesh, math, random, sys, time
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:]
N = int(argv[0]); OUT = argv[1]; SAMPLES = int(argv[2]); RES = int(argv[3])
random.seed(7)
R = 1.0

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene


def node_mat(name):
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    nt.links.new(bsdf.outputs[0], out.inputs[0])
    return m, nt, bsdf


def p0_socket(nt):
    # Parçanın orijini kaydırılsa da doku karpuzun ilk uzayında kalsın: p0 = obje koord. + obj["off"]
    tc = nt.nodes.new("ShaderNodeTexCoord")
    at = nt.nodes.new("ShaderNodeAttribute"); at.attribute_type = "OBJECT"; at.attribute_name = "off"
    add = nt.nodes.new("ShaderNodeVectorMath"); add.operation = "ADD"
    nt.links.new(tc.outputs["Object"], add.inputs[0]); nt.links.new(at.outputs["Vector"], add.inputs[1])
    return add.outputs[0]


def math(nt, op, a, b=None, v=None):
    n = nt.nodes.new("ShaderNodeMath"); n.operation = op
    nt.links.new(a, n.inputs[0])
    if b is not None: nt.links.new(b, n.inputs[1])
    if v is not None: n.inputs[1].default_value = v
    return n.outputs[0]


# --- kabuk: koyu/açık yeşil zikzak şeritler
rind, nt, b = node_mat("rind")
p = p0_socket(nt)
sep = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(p, sep.inputs[0])
ang = math(nt, "ARCTAN2", sep.outputs[1], sep.outputs[0])
noi = nt.nodes.new("ShaderNodeTexNoise"); noi.inputs["Scale"].default_value = 3.5; noi.inputs["Detail"].default_value = 6
nt.links.new(p, noi.inputs["Vector"])
warp = math(nt, "MULTIPLY", noi.outputs["Fac"], v=1.6)
a2 = math(nt, "ADD", math(nt, "MULTIPLY", ang, v=8.0), warp)
s = math(nt, "SINE", a2)
ramp = nt.nodes.new("ShaderNodeValToRGB"); nt.links.new(s, ramp.inputs[0])
ramp.color_ramp.elements[0].position = 0.42; ramp.color_ramp.elements[0].color = (0.010, 0.045, 0.010, 1)
ramp.color_ramp.elements[1].position = 0.58; ramp.color_ramp.elements[1].color = (0.12, 0.32, 0.05, 1)
nt.links.new(ramp.outputs[0], b.inputs["Base Color"])
b.inputs["Roughness"].default_value = 0.32
bump = nt.nodes.new("ShaderNodeBump"); bump.inputs["Strength"].default_value = 0.08
nt.links.new(noi.outputs["Fac"], bump.inputs["Height"]); nt.links.new(bump.outputs[0], b.inputs["Normal"])

# --- iç: kırmızı et, kenarda beyaz kabuk bandı, çekirdekler, SSS
flesh, nt, b = node_mat("flesh")
p = p0_socket(nt)
ln = nt.nodes.new("ShaderNodeVectorMath"); ln.operation = "LENGTH"; nt.links.new(p, ln.inputs[0])
r = nt.nodes.new("ShaderNodeValToRGB"); nt.links.new(ln.outputs["Value"], r.inputs[0])
cr = r.color_ramp
cr.elements[0].position = 0.80; cr.elements[0].color = (0.55, 0.02, 0.04, 1)
cr.elements[1].position = 0.86; cr.elements[1].color = (0.85, 0.80, 0.62, 1)
e = cr.elements.new(0.94); e.color = (0.80, 0.86, 0.60, 1)
e = cr.elements.new(0.97); e.color = (0.03, 0.12, 0.02, 1)
vor = nt.nodes.new("ShaderNodeTexVoronoi"); vor.inputs["Scale"].default_value = 7.0
nt.links.new(p, vor.inputs["Vector"])
seed = math(nt, "LESS_THAN", vor.outputs["Distance"], v=0.07)
band = math(nt, "MULTIPLY", math(nt, "GREATER_THAN", ln.outputs["Value"], v=0.35), math(nt, "LESS_THAN", ln.outputs["Value"], v=0.70))
seedm = math(nt, "MULTIPLY", seed, band)
mix = nt.nodes.new("ShaderNodeMix"); mix.data_type = "RGBA"
nt.links.new(seedm, mix.inputs["Factor"]); nt.links.new(r.outputs[0], mix.inputs[6])
mix.inputs[7].default_value = (0.01, 0.008, 0.006, 1)
nt.links.new(mix.outputs[2], b.inputs["Base Color"])
gr = nt.nodes.new("ShaderNodeTexNoise"); gr.inputs["Scale"].default_value = 40; gr.inputs["Detail"].default_value = 4
nt.links.new(p, gr.inputs["Vector"])
rough = math(nt, "ADD", math(nt, "MULTIPLY", gr.outputs["Fac"], v=0.35), v=0.05)
nt.links.new(rough, b.inputs["Roughness"])
b.inputs["Subsurface Weight"].default_value = 0.35
b.inputs["Subsurface Radius"].default_value = (0.6, 0.12, 0.08)
b.inputs["Subsurface Scale"].default_value = 0.05
bump = nt.nodes.new("ShaderNodeBump"); bump.inputs["Strength"].default_value = 0.25
nt.links.new(gr.outputs["Fac"], bump.inputs["Height"]); nt.links.new(bump.outputs[0], b.inputs["Normal"])

# --- karpuz gövdesi
bm = bmesh.new()
bmesh.ops.create_uvsphere(bm, u_segments=96, v_segments=64, radius=R)
for v in bm.verts:
    v.co.z *= 0.93
for f in bm.faces:
    f.material_index = 0
    f.smooth = True


def cut(bm_src, co, no, keep_pos):
    b2 = bm_src.copy()
    geom = b2.verts[:] + b2.edges[:] + b2.faces[:]
    res = bmesh.ops.bisect_plane(b2, geom=geom, plane_co=co, plane_no=no,
                                 clear_inner=keep_pos, clear_outer=not keep_pos)
    edges = [g for g in res["geom_cut"] if isinstance(g, bmesh.types.BMEdge)]
    if not b2.faces:
        b2.free(); return None
    if edges:
        new = bmesh.ops.edgeloop_fill(b2, edges=edges)["faces"]
        for f in new:
            f.material_index = 1; f.smooth = False
    return b2


pieces = [bm]
for i in range(N):
    no = Vector((random.uniform(-1, 1), random.uniform(-1, 1), random.uniform(-0.6, 0.6))).normalized()
    co = Vector((random.uniform(-.45, .45), random.uniform(-.45, .45), random.uniform(-.3, .3)))
    nxt = []
    for pb in pieces:
        side = [v.co.dot(no) - co.dot(no) for v in pb.verts]
        if min(side) > 0 or max(side) < 0:
            nxt.append(pb); continue
        for k in (True, False):
            q = cut(pb, co, no, k)
            if q and len(q.faces) > 2:
                nxt.append(q)
        pb.free()
    pieces = nxt

LIFT = Vector((0, 0, 0.12 + R * 0.93))
for i, pb in enumerate(pieces):
    me = bpy.data.meshes.new(f"p{i}"); pb.to_mesh(me); pb.free()
    me.materials.append(rind); me.materials.append(flesh)
    c = sum((v.co for v in me.vertices), Vector()) / len(me.vertices)
    for v in me.vertices:
        v.co -= c
    ob = bpy.data.objects.new(f"p{i}", me); sc.collection.objects.link(ob)
    ob["off"] = list(c)
    # patlama anı: merkezden dışarı + rastgele dönüş
    d = c.normalized() if c.length > 1e-3 else Vector((0, 0, 1))
    k = 0.0 if N == 0 else 0.55
    ob.location = c + LIFT + d * k * (0.6 + random.random() * 0.6)
    ob.rotation_euler = [random.uniform(-.5, .5) * (k > 0) for _ in range(3)]

# --- kesme tahtası (ahşap)
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0.06))
board = bpy.context.object; board.scale = (2.6, 1.5, 0.12)
bm_ = board.modifiers.new("bev", "BEVEL"); bm_.width = 0.035; bm_.segments = 4
bpy.ops.object.transform_apply(scale=True)
wood, nt, b = node_mat("wood")
w = nt.nodes.new("ShaderNodeTexWave"); w.wave_type = "BANDS"; w.bands_direction = "X"
w.inputs["Scale"].default_value = 1.2; w.inputs["Distortion"].default_value = 9; w.inputs["Detail"].default_value = 3
tc = nt.nodes.new("ShaderNodeTexCoord"); nt.links.new(tc.outputs["Object"], w.inputs["Vector"])
wr = nt.nodes.new("ShaderNodeValToRGB"); nt.links.new(w.outputs["Fac"], wr.inputs[0])
wr.color_ramp.elements[0].color = (0.33, 0.15, 0.06, 1); wr.color_ramp.elements[1].color = (0.55, 0.30, 0.14, 1)
nt.links.new(wr.outputs[0], b.inputs["Base Color"]); b.inputs["Roughness"].default_value = 0.55
board.data.materials.append(wood)

# --- zemin + dünya (koyu gri stüdyo)
bpy.ops.mesh.primitive_plane_add(size=60)
floor = bpy.context.object
fm, nt, b = node_mat("floor"); b.inputs["Base Color"].default_value = (0.045, 0.045, 0.05, 1); b.inputs["Roughness"].default_value = 0.6
floor.data.materials.append(fm)
world = bpy.data.worlds.new("w"); sc.world = world; world.use_nodes = True
world.node_tree.nodes["Background"].inputs[0].default_value = (0.03, 0.03, 0.034, 1)

# --- ışıklar
def area(loc, size, energy, rot_to=Vector((0, 0, 1))):
    l = bpy.data.lights.new("a", "AREA"); l.size = size; l.energy = energy
    o = bpy.data.objects.new("a", l); sc.collection.objects.link(o); o.location = loc
    o.rotation_euler = (Vector(rot_to) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
area((-2.5, -3.0, 5.0), 4.0, 900)
area((3.5, 2.5, 3.0), 2.5, 500)
area((0.0, 4.0, 2.0), 3.0, 250)

# --- kamera (dikey 9:16)
cd = bpy.data.cameras.new("c"); cd.lens = 50; cd.dof.use_dof = True; cd.dof.aperture_fstop = 5.6
cam = bpy.data.objects.new("c", cd); sc.collection.objects.link(cam); sc.camera = cam
cam.location = (0, -8.8, 3.2)
cam.rotation_euler = (Vector((0, 0, 1.3)) - cam.location).to_track_quat("-Z", "Y").to_euler()
cd.dof.focus_distance = (cam.location - Vector((0, 0, 1.1))).length

sc.render.engine = "CYCLES"; sc.cycles.device = "CPU"
sc.cycles.samples = SAMPLES; sc.cycles.use_denoising = True; sc.cycles.denoiser = "OPENIMAGEDENOISE"
sc.render.resolution_x = 1080; sc.render.resolution_y = 1920; sc.render.resolution_percentage = RES
sc.view_settings.view_transform = "AgX"; sc.view_settings.look = "AgX - Medium High Contrast"
sc.render.filepath = OUT
t = time.time()
bpy.ops.render.render(write_still=True)
print(f"PIECES={len(pieces)} RENDER_SEC={time.time() - t:.1f}")
