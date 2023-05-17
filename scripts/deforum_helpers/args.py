from modules.shared import cmd_opts
from modules.processing import get_fixed_seed
import modules.shared as sh
import modules.paths as ph
import os
import time
import json
from types import SimpleNamespace
from .general_utils import get_os, get_deforum_version, substitute_placeholders
from .deforum_controlnet import controlnet_component_names
from .defaults import get_guided_imgs_default_json, mask_fill_choices
import tempfile
       
def RootArgs():
    device = sh.device
    models_path = ph.models_path + '/Deforum'
    half_precision = not cmd_opts.no_half
    mask_preset_names = ['everywhere','video_mask']
    p = None
    frames_cache = []
    raw_batch_name = None
    raw_seed = None
    initial_seed = None
    initial_info = None
    first_frame = None
    outpath_samples = ""
    animation_prompts = None
    color_corrections = None 
    initial_clipskip = None
    current_user_os = get_os()
    tmp_deforum_run_duplicated_folder = os.path.join(tempfile.gettempdir(), 'tmp_run_deforum')
    return locals()

def DeforumAnimArgs():
    animation_mode = '2D' # ['None', '2D', '3D', 'Video Input', 'Interpolation']
    max_frames = 120 
    border = 'replicate' # ['wrap', 'replicate']
    angle = "0:(0)"
    zoom = "0:(1.0025+0.002*sin(1.25*3.14*t/30))"
    translation_x = "0:(0)"
    translation_y = "0:(0)"
    translation_z = "0:(1.75)"
    transform_center_x = "0:(0.5)"
    transform_center_y = "0:(0.5)"
    rotation_3d_x = "0:(0)"
    rotation_3d_y = "0:(0)"
    rotation_3d_z = "0:(0)"
    enable_perspective_flip = False 
    perspective_flip_theta = "0:(0)"
    perspective_flip_phi = "0:(0)"
    perspective_flip_gamma = "0:(0)"
    perspective_flip_fv = "0:(53)"
    noise_schedule = "0: (0.065)"
    strength_schedule = "0: (0.65)"
    contrast_schedule = "0: (1.0)"
    cfg_scale_schedule = "0: (7)"
    enable_steps_scheduling = False
    steps_schedule = "0: (25)"
    fov_schedule = "0: (70)"
    aspect_ratio_schedule = "0: (1)"
    aspect_ratio_use_old_formula = False
    near_schedule = "0: (200)"
    far_schedule = "0: (10000)"
    seed_schedule = '0:(s), 1:(-1), "max_f-2":(-1), "max_f-1":(s)'
    pix2pix_img_cfg_scale = "1.5"
    pix2pix_img_cfg_scale_schedule = "0:(1.5)"
    enable_subseed_scheduling = False
    subseed_schedule = "0:(1)"
    subseed_strength_schedule = "0:(0)"
    # Sampler Scheduling
    enable_sampler_scheduling = False 
    sampler_schedule = '0: ("Euler a")'
    # Composable mask scheduling
    use_noise_mask = False
    mask_schedule = '0: ("{video_mask}")'
    noise_mask_schedule = '0: ("{video_mask}")'
    # Checkpoint Scheduling
    enable_checkpoint_scheduling = False
    checkpoint_schedule = '0: ("model1.ckpt"), 100: ("model2.safetensors")'
    # CLIP skip Scheduling
    enable_clipskip_scheduling = False 
    clipskip_schedule = '0: (2)'
    # Noise Multiplier Scheduling
    enable_noise_multiplier_scheduling = True
    noise_multiplier_schedule = '0: (1.05)'
    # Anti-blur
    amount_schedule = "0: (0.1)"
    kernel_schedule = "0: (5)"
    sigma_schedule = "0: (1.0)"
    threshold_schedule = "0: (0.0)"
    # Hybrid video
    hybrid_comp_alpha_schedule = "0:(0.5)" 
    hybrid_comp_mask_blend_alpha_schedule = "0:(0.5)" 
    hybrid_comp_mask_contrast_schedule = "0:(1)" 
    hybrid_comp_mask_auto_contrast_cutoff_high_schedule = "0:(100)" 
    hybrid_comp_mask_auto_contrast_cutoff_low_schedule = "0:(0)"
    hybrid_flow_factor_schedule = "0:(1)"
    #Coherence
    color_coherence = 'LAB' # ['None', 'HSV', 'LAB', 'RGB', 'Video Input', 'Image']
    color_coherence_image_path = ""
    color_coherence_video_every_N_frames = 1
    color_force_grayscale = False 
    legacy_colormatch = False 
    diffusion_cadence = '2' #['1','2','3','4','5','6','7','8']
    optical_flow_cadence = 'None' #['None', 'RAFT','DIS Medium', 'DIS Fine', 'Farneback']
    cadence_flow_factor_schedule = "0: (1)"
    optical_flow_redo_generation = 'None' #['None', 'RAFT', 'DIS Medium', 'DIS Fine', 'Farneback']
    redo_flow_factor_schedule = "0: (1)"
    diffusion_redo = '0'
    #**Noise settings:**
    noise_type = 'perlin' # ['uniform', 'perlin']
    # Perlin params
    perlin_w = 8 
    perlin_h = 8 
    perlin_octaves = 4 
    perlin_persistence = 0.5 
    #**3D Depth Warping:**
    use_depth_warping = True 
    depth_algorithm = 'Midas-3-Hybrid' # ['Midas+AdaBins (old)','Zoe+AdaBins (old)', 'Midas-3-Hybrid','Midas-3.1-BeitLarge', 'AdaBins', 'Zoe', 'Leres'] Midas-3.1-BeitLarge is temporarily removed 04-05-23 until fixed
    midas_weight = 0.2 # midas/ zoe weight - only relevant in old/ legacy depth_algorithm modes. see above ^
    padding_mode = 'border' # ['border', 'reflection', 'zeros'] 
    sampling_mode = 'bicubic' # ['bicubic', 'bilinear', 'nearest']
    save_depth_maps = False 
    #**Video Input:**
    video_init_path ='https://deforum.github.io/a1/V1.mp4' 
    extract_nth_frame = 1
    extract_from_frame = 0 
    extract_to_frame = -1  # minus 1 for unlimited frames
    overwrite_extracted_frames = True 
    use_mask_video = False 
    video_mask_path ='https://deforum.github.io/a1/VM1.mp4'
    #**Hybrid Video for 2D/3D Animation Mode:**
    hybrid_generate_inputframes = False 
    hybrid_generate_human_masks = "None" #['None','PNGs','Video', 'Both']
    hybrid_use_first_frame_as_init_image = True 
    hybrid_motion = "None" #['None','Optical Flow','Perspective','Affine']
    hybrid_motion_use_prev_img = False 
    hybrid_flow_consistency = False
    hybrid_consistency_blur = 2
    hybrid_flow_method = "RAFT" #['RAFT', 'DIS Medium', 'DIS Fine', 'Farneback']
    hybrid_composite = 'None' #['None', 'Normal', 'Before Motion', 'After Generation'] 
    hybrid_use_init_image = False 
    hybrid_comp_mask_type = "None" #['None', 'Depth', 'Video Depth', 'Blend', 'Difference']
    hybrid_comp_mask_inverse = False 
    hybrid_comp_mask_equalize = "None" # ['None','Before','After','Both']
    hybrid_comp_mask_auto_contrast = False 
    hybrid_comp_save_extra_frames = False 
    resume_from_timestring = False 
    resume_timestring = "20230129210106" 
    enable_ddim_eta_scheduling = False
    ddim_eta_schedule = "0:(0)"
    enable_ancestral_eta_scheduling = False
    ancestral_eta_schedule = "0:(1)"

    return locals()
    
def DeforumArgs():
    # set default image size and make sure to resize to multiples of 64 if needed
    W, H = map(lambda x: x - x % 64, (512, 512))
    
    # wether or not to show gradio's info section for all params in the ui. it's a realtime toggle
    show_info_on_ui = True

    #**Webui stuff**
    tiling = False
    restore_faces = False
    seed_enable_extras = False
    subseed = -1
    subseed_strength = 0
    seed_resize_from_w = 0
    seed_resize_from_h = 0
    
    #**Sampling Settings**
    seed = -1 #
    sampler = 'euler_ancestral' # ["klms","dpm2","dpm2_ancestral","heun","euler","euler_ancestral","plms", "ddim"]
    steps = 25 #
    scale = 7 #
    
    #**Save & Display Settings**
    save_settings = True 
    save_sample_per_step = False

    #**Batch Settings**
    n_batch = 1 #
    batch_name = "Deforum_{timestring}" 
    seed_behavior = "iter" # ["iter","fixed","random","ladder","alternate","schedule"]
    seed_iter_N = 1
    outdir = ""

    #**Init Settings**
    use_init = False
    strength = 0.8
    strength_0_no_init = True # Set the strength to 0 automatically when no init image is used
    init_image = "https://deforum.github.io/a1/I1.png" 
    # Whiter areas of the mask are areas that change more
    use_mask = False 
    use_alpha_as_mask = False # use the alpha channel of the init image as the mask
    mask_file = "https://deforum.github.io/a1/M1.jpg" 
    invert_mask = False 
    # Adjust mask image, 1.0 is no adjustment. Should be positive numbers.
    mask_contrast_adjust = 1.0  
    mask_brightness_adjust = 1.0  
    # Overlay the masked image at the end of the generation so it does not get degraded by encoding and decoding
    overlay_mask = True 
    # Blur edges of final overlay mask, if used. Minimum = 0 (no blur)
    mask_overlay_blur = 4

    fill = 1 #MASKARGSEXPANSION Todo : Rename and convert to same formatting as used in img2img masked content
    full_res_mask = True
    full_res_mask_padding = 4
    reroll_blank_frames = 'reroll' # reroll, interrupt, or ignore
    reroll_patience = 10

    prompt = ""
    timestring = ""
    init_sample = None
    mask_image = None
    noise_mask = None
    seed_internal = 0

    return locals()

def LoopArgs():
    use_looper = False
    init_images = get_guided_imgs_default_json()
    image_strength_schedule = "0:(0.75)"
    blendFactorMax = "0:(0.35)"
    blendFactorSlope = "0:(0.25)"
    tweening_frames_schedule = "0:(20)"
    color_correction_factor = "0:(0.075)"
    return locals()

def ParseqArgs():
    parseq_manifest = None
    parseq_use_deltas = True
    return locals()
    
def DeforumOutputArgs():
    skip_video_creation = False
    fps = 15 
    make_gif = False
    delete_imgs = False # True will delete all imgs after a successful mp4 creation
    image_path = "C:/SD/20230124234916_%09d.png" 
    mp4_path = "testvidmanualsettings.mp4" 
    add_soundtrack = 'None' # ["File","Init Video"]
    soundtrack_path = "https://deforum.github.io/a1/A1.mp3"
    # End-Run upscaling
    r_upscale_video = False
    r_upscale_factor = 'x2' # ['2x', 'x3', 'x4']
    r_upscale_model = 'realesr-animevideov3' # 'realesr-animevideov3' (default of realesrgan engine, does 2-4x), the rest do only 4x: 'realesrgan-x4plus', 'realesrgan-x4plus-anime'
    r_upscale_keep_imgs = True
    
    store_frames_in_ram = False
    #**Interpolate Video Settings**
    frame_interpolation_engine = "None" # ["None", "RIFE v4.6", "FILM"]
    frame_interpolation_x_amount = 2 # [2 to 1000 depends on the engine]
    frame_interpolation_slow_mo_enabled = False
    frame_interpolation_slow_mo_amount = 2 #[2 to 10]
    frame_interpolation_keep_imgs = False
    return locals()

i1_store_backup = f"<p style=\"text-align:center;font-weight:bold;margin-bottom:0em\">Deforum extension for auto1111 — version 2.4b | Git commit: {get_deforum_version()}</p>"
i1_store = i1_store_backup

d = SimpleNamespace(**DeforumArgs()) #default args
da = SimpleNamespace(**DeforumAnimArgs()) #default anim args
dp = SimpleNamespace(**ParseqArgs()) #default parseq ars
dv = SimpleNamespace(**DeforumOutputArgs()) #default video args
dr = SimpleNamespace(**RootArgs()) # ROOT args
dloopArgs = SimpleNamespace(**LoopArgs())

anim_args_names =   str(r'''animation_mode, max_frames, border,
                        angle, zoom, translation_x, translation_y, translation_z, transform_center_x, transform_center_y,
                        rotation_3d_x, rotation_3d_y, rotation_3d_z,
                        enable_perspective_flip, enable_ddim_eta_scheduling, ddim_eta_schedule, enable_ancestral_eta_scheduling, ancestral_eta_schedule,
                        perspective_flip_theta, perspective_flip_phi, perspective_flip_gamma, perspective_flip_fv,
                        noise_schedule, strength_schedule, contrast_schedule, cfg_scale_schedule, pix2pix_img_cfg_scale_schedule,
                        enable_subseed_scheduling, subseed_schedule, subseed_strength_schedule,
                        enable_steps_scheduling, steps_schedule,
                        fov_schedule, aspect_ratio_schedule, aspect_ratio_use_old_formula, near_schedule, far_schedule,
                        seed_schedule,
                        enable_sampler_scheduling, sampler_schedule,
                        mask_schedule, use_noise_mask, noise_mask_schedule,
                        enable_checkpoint_scheduling, checkpoint_schedule,
                        enable_clipskip_scheduling, clipskip_schedule, enable_noise_multiplier_scheduling, noise_multiplier_schedule,
                        kernel_schedule, sigma_schedule, amount_schedule, threshold_schedule,
                        color_coherence, color_coherence_image_path, color_coherence_video_every_N_frames, color_force_grayscale, legacy_colormatch,
                        diffusion_cadence, optical_flow_cadence, cadence_flow_factor_schedule,
                        optical_flow_redo_generation, redo_flow_factor_schedule, diffusion_redo,
                        noise_type, perlin_w, perlin_h, perlin_octaves, perlin_persistence,
                        use_depth_warping, depth_algorithm ,midas_weight,
                        padding_mode, sampling_mode, save_depth_maps,
                        video_init_path, extract_nth_frame, extract_from_frame, extract_to_frame, overwrite_extracted_frames,
                        use_mask_video, video_mask_path,
                        resume_from_timestring, resume_timestring'''
                    ).replace("\n", "").replace("\r", "").replace(" ", "").split(',')
hybrid_args_names = str(r'''hybrid_generate_inputframes, hybrid_generate_human_masks, hybrid_use_first_frame_as_init_image,
                        hybrid_motion, hybrid_motion_use_prev_img, hybrid_flow_consistency, hybrid_consistency_blur, hybrid_flow_method, hybrid_composite,
                        hybrid_use_init_image, hybrid_comp_mask_type, hybrid_comp_mask_inverse,
                        hybrid_comp_mask_equalize, hybrid_comp_mask_auto_contrast, hybrid_comp_save_extra_frames,
                        hybrid_comp_alpha_schedule, hybrid_flow_factor_schedule,
                        hybrid_comp_mask_blend_alpha_schedule, hybrid_comp_mask_contrast_schedule,
                        hybrid_comp_mask_auto_contrast_cutoff_high_schedule, hybrid_comp_mask_auto_contrast_cutoff_low_schedule'''
                    ).replace("\n", "").replace("\r", "").replace(" ", "").split(',')
args_names =        str(r'''W, H, tiling, restore_faces, seed, sampler, seed_enable_extras,
                        seed_resize_from_w, seed_resize_from_h, steps, n_batch, save_settings,
                        save_sample_per_step, batch_name, seed_behavior, seed_iter_N, use_init, strength_0_no_init, strength, init_image,
                        use_mask, use_alpha_as_mask, invert_mask, overlay_mask,
                        mask_file, mask_contrast_adjust, mask_brightness_adjust, mask_overlay_blur,
                        fill, full_res_mask, full_res_mask_padding, reroll_blank_frames,reroll_patience'''
                    ).replace("\n", "").replace("\r", "").replace(" ", "").split(',')
video_args_names =  str(r'''skip_video_creation,
                            fps, make_gif, delete_imgs, add_soundtrack, soundtrack_path, r_upscale_video, r_upscale_model, r_upscale_factor, r_upscale_keep_imgs,
                            store_frames_in_ram, frame_interpolation_engine, frame_interpolation_x_amount, frame_interpolation_slow_mo_enabled, frame_interpolation_slow_mo_amount, frame_interpolation_keep_imgs'''
                    ).replace("\n", "").replace("\r", "").replace(" ", "").split(',')
parseq_args_names = str(r'''parseq_manifest, parseq_use_deltas'''
                    ).replace("\n", "").replace("\r", "").replace(" ", "").split(',')
loop_args_names =   str(r'''use_looper, init_images, image_strength_schedule, blendFactorMax, blendFactorSlope, 
                          tweening_frames_schedule, color_correction_factor'''
                    ).replace("\n", "").replace("\r", "").replace(" ", "").split(',')

def get_component_names():
    return ['override_settings_with_file', 'custom_settings_file'] + anim_args_names +['animation_prompts', 'animation_prompts_positive', 'animation_prompts_negative'] + args_names + video_args_names + parseq_args_names + hybrid_args_names + loop_args_names + controlnet_component_names()

def get_settings_component_names():
    return [name for name in get_component_names()] #if name not in video_args_names]
    
def setup_deforum_setting_ui(is_img2img):
    from .ui_left import setup_deforum_setting_dictionary
    ds = setup_deforum_setting_dictionary(is_img2img,d,da,dp,dv,dr,dloopArgs)
    return [ds[name] for name in (['btn'] + get_component_names())]
    
def pack_args(args_dict):
    args_dict = {name: args_dict[name] for name in args_names}
    args_dict['subseed'] = -1
    args_dict['subseed_strength'] = 0
    args_dict['timestring'] = ""
    args_dict['init_sample'] = None
    args_dict['noise_mask'] = None
    args_dict['seed_internal'] = 0
    return args_dict
    
def pack_anim_args(args_dict):
    return {name: args_dict[name] for name in (anim_args_names + hybrid_args_names)}
   
def pack_video_args(args_dict):
    return {name: args_dict[name] for name in video_args_names}

def pack_parseq_args(args_dict):
    return {name: args_dict[name] for name in parseq_args_names}
    
def pack_loop_args(args_dict):
    return {name: args_dict[name] for name in loop_args_names}

def pack_controlnet_args(args_dict):
    return {name: args_dict[name] for name in controlnet_component_names()}

def process_args(args_dict_main, run_id):
    from deforum_helpers.settings import load_args
    override_settings_with_file = args_dict_main['override_settings_with_file']
    custom_settings_file = args_dict_main['custom_settings_file']
    args_dict = pack_args(args_dict_main)
    anim_args_dict = pack_anim_args(args_dict_main)
    video_args_dict = pack_video_args(args_dict_main)
    parseq_args_dict = pack_parseq_args(args_dict_main)
    loop_args_dict = pack_loop_args(args_dict_main)
    controlnet_args_dict = pack_controlnet_args(args_dict_main)
    
    root = SimpleNamespace(**RootArgs())
    root.p = args_dict_main['p']
    p = root.p
    root.animation_prompts = json.loads(args_dict_main['animation_prompts'])
    
    args_loaded_ok = True # can use this later to error cleanly upon wrong gen param in ui
    if override_settings_with_file:
        args_loaded_ok = load_args(args_dict_main, args_dict, anim_args_dict, parseq_args_dict, loop_args_dict, controlnet_args_dict, video_args_dict, custom_settings_file, root, run_id)
        
    positive_prompts = args_dict_main['animation_prompts_positive']
    negative_prompts = args_dict_main['animation_prompts_negative']
    negative_prompts = negative_prompts.replace('--neg', '') # remove --neg from negative_prompts if recieved by mistake
    for key in root.animation_prompts:
        animationPromptCurr = root.animation_prompts[key]
        root.animation_prompts[key] = f"{positive_prompts} {animationPromptCurr} {'' if '--neg' in animationPromptCurr else '--neg'} {negative_prompts}"
    root.positive_prompts = positive_prompts
    root.negative_prompts = negative_prompts
    
    os.makedirs(root.models_path, exist_ok=True)

    args = SimpleNamespace(**args_dict)
    anim_args = SimpleNamespace(**anim_args_dict)
    video_args = SimpleNamespace(**video_args_dict)
    parseq_args = SimpleNamespace(**parseq_args_dict)
    loop_args = SimpleNamespace(**loop_args_dict)
    controlnet_args = SimpleNamespace(**controlnet_args_dict)

    p.width, p.height = map(lambda x: x - x % 8, (args.W, args.H))
    p.steps = args.steps
    p.seed = args.seed
    p.sampler_name = args.sampler
    p.batch_size = args.n_batch
    p.tiling = args.tiling
    p.restore_faces = args.restore_faces
    p.seed_enable_extras = args.seed_enable_extras
    p.subseed = args.subseed
    p.subseed_strength = args.subseed_strength
    p.seed_resize_from_w = args.seed_resize_from_w
    p.seed_resize_from_h = args.seed_resize_from_h
    p.fill = args.fill
    if args.seed == -1:
        root.raw_seed = -1
    args.seed = get_fixed_seed(args.seed)
    if root.raw_seed != -1:
        root.raw_seed = args.seed
    args.timestring = time.strftime('%Y%m%d%H%M%S')
    args.strength = max(0.0, min(1.0, args.strength))
    args.prompts = json.loads(args_dict_main['animation_prompts'])
    args.positive_prompts = args_dict_main['animation_prompts_positive']
    args.negative_prompts = args_dict_main['animation_prompts_negative']

    if not args.use_init and not anim_args.hybrid_use_init_image:
        args.init_image = None
        
    if anim_args.animation_mode == 'None':
        anim_args.max_frames = 1
    elif anim_args.animation_mode == 'Video Input':
        args.use_init = True
    
    current_arg_list = [args, anim_args, video_args, parseq_args]
    full_base_folder_path = os.path.join(os.getcwd(), p.outpath_samples)
    root.raw_batch_name = args.batch_name
    args.batch_name = substitute_placeholders(args.batch_name, current_arg_list, full_base_folder_path)
    args.outdir = os.path.join(p.outpath_samples, str(args.batch_name))
    root.outpath_samples = args.outdir
    args.outdir = os.path.join(os.getcwd(), args.outdir)
    os.makedirs(args.outdir, exist_ok=True)
    
    return args_loaded_ok, root, args, anim_args, video_args, parseq_args, loop_args, controlnet_args