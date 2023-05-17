import os, sys
from .args import d, da, dp, dv, dr, dloopArgs, i1_store, i1_store_backup, get_component_names, get_settings_component_names, video_args_names
from modules.ui import create_output_panel
from modules.shared import opts, state
from modules.ui import create_output_panel, wrap_gradio_call
from webui import wrap_gradio_gpu_call
from .run_deforum import run_deforum
from .settings import save_settings, load_all_settings, load_video_settings

import gradio as gr

deforum_folder_name = os.path.sep.join(os.path.abspath(__file__).split(os.path.sep)[:-3])
basedirs = [os.getcwd()]

def on_ui_tabs():
    if 'google.colab' in sys.modules:
        basedirs.append('/content/gdrive/MyDrive/sd/stable-diffusion-webui') #hardcode as TheLastBen's colab seems to be the primal source
    for basedir in basedirs:
        sys.path.extend([os.path.join(deforum_folder_name, 'scripts', 'deforum_helpers', 'src')])
    from deforum_helpers.ui import setup_deforum_setting_dictionary
    with gr.Blocks(analytics_enabled=False) as deforum_interface:
        components = {}
        dummy_component = gr.Label(visible=False)
        with gr.Row(elem_id='deforum_progress_row').style(equal_height=False, variant='compact'):
            with gr.Column(scale=1, variant='panel'):
                components = setup_deforum_setting_dictionary(True, d, da,dp,dv,dr,dloopArgs)
        
            with gr.Column(scale=1, variant='compact'):
                with gr.Row(variant='compact'):
                    btn = gr.Button("Click here after the generation to show the video")
                    components['btn'] = btn
                    close_btn = gr.Button("Close the video", visible=False)
                with gr.Row(variant='compact'):
                    i1 = gr.HTML(i1_store, elem_id='deforum_header')
                    components['i1'] = i1
                    # Show video
                    def show_vid():
                        return {
                            i1: gr.update(value=i1_store, visible=True),
                            close_btn: gr.update(visible=True),
                            btn: gr.update(value="Update the video", visible=True),
                        }
                
                    btn.click(
                        show_vid,
                        [],
                        [i1, close_btn, btn],
                        )
                    # Close video
                    def close_vid():
                        return {
                            i1: gr.update(value=i1_store_backup, visible=True),
                            close_btn: gr.update(visible=False),
                            btn: gr.update(value="Click here after the generation to show the video", visible=True),
                        }
                    
                    close_btn.click(
                        close_vid,
                        [],
                        [i1, close_btn, btn],
                        )
                id_part = 'deforum'
                with gr.Row(elem_id=f"{id_part}_generate_box", variant='compact'):
                    skip = gr.Button('Pause/Resume', elem_id=f"{id_part}_skip", visible=False)
                    interrupt = gr.Button('Interrupt', elem_id=f"{id_part}_interrupt", visible=True)
                    submit = gr.Button('Generate', elem_id=f"{id_part}_generate", variant='primary')

                    skip.click(
                        fn=lambda: state.skip(),
                        inputs=[],
                        outputs=[],
                    )

                    interrupt.click(
                        fn=lambda: state.interrupt(),
                        inputs=[],
                        outputs=[],
                    )
                
                deforum_gallery, generation_info, html_info, html_log = create_output_panel("deforum", opts.outdir_img2img_samples)

                with gr.Row(variant='compact'):
                    settings_path = gr.Textbox("deforum_settings.txt", elem_id='deforum_settings_path', label="Settings File", info="settings file path can be relative to webui folder OR full - absolute")
                    #reuse_latest_settings_btn = gr.Button('Reuse Latest', elem_id='deforum_reuse_latest_settings_btn')#TODO
                with gr.Row(variant='compact'):
                    save_settings_btn = gr.Button('Save Settings', elem_id='deforum_save_settings_btn')
                    load_settings_btn = gr.Button('Load All Settings', elem_id='deforum_load_settings_btn')
                    load_video_settings_btn = gr.Button('Load Video Settings', elem_id='deforum_load_video_settings_btn')

        component_list = [components[name] for name in get_component_names()]

        submit.click(
                    fn=wrap_gradio_gpu_call(run_deforum, extra_outputs=[None, '', '']),
                    _js="submit_deforum",
                    inputs=[dummy_component, dummy_component] + component_list,
                    outputs=[
                         deforum_gallery,
                         components["resume_timestring"],
                         generation_info,
                         html_info,
                         html_log,
                    ],
                )
        
        settings_component_list = [components[name] for name in get_settings_component_names()]
        video_settings_component_list = [components[name] for name in video_args_names]
        stuff = gr.HTML("") # wrap gradio call garbage
        stuff.visible = False

        save_settings_btn.click(
            fn=wrap_gradio_call(save_settings),
            inputs=[settings_path] + settings_component_list + video_settings_component_list,
            outputs=[stuff],
        )
        
        load_settings_btn.click(
        fn=wrap_gradio_call(lambda *args, **kwargs: load_all_settings(*args, ui_launch=False, **kwargs)),
        inputs=[settings_path] + settings_component_list,
        outputs=settings_component_list + [stuff],
        )

        load_video_settings_btn.click(
            fn=wrap_gradio_call(load_video_settings),
            inputs=[settings_path] + video_settings_component_list,
            outputs=video_settings_component_list + [stuff],
        )
        
    def trigger_load_general_settings():
        print("Loading general settings...")
        wrapped_fn = wrap_gradio_call(lambda *args, **kwargs: load_all_settings(*args, ui_launch=True, **kwargs))
        inputs = [settings_path.value] + [component.value for component in settings_component_list]
        outputs = settings_component_list + [stuff]
        updated_values = wrapped_fn(*inputs, *outputs)[0]

        settings_component_name_to_obj = {name: component for name, component in zip(get_settings_component_names(), settings_component_list)}
        for key, value in updated_values.items():
            settings_component_name_to_obj[key].value = value['value']

            
    if opts.data.get("deforum_enable_persistent_settings", False):
        trigger_load_general_settings()
        
    return [(deforum_interface, "Deforum", "deforum_interface")]