"""
Configuration file builder for Interactive Wand setup.

Constructs config.yaml structure from user inputs.
"""


def build_final_config(hw_config: dict, detect_config: dict, audio_config: dict) -> dict:
    """
    Build complete configuration structure from component configs.

    Args:
        hw_config: Hardware configuration dict
        detect_config: Detection parameters dict
        audio_config: Audio settings dict

    Returns:
        Complete config structure ready for YAML serialization
    """
    return {
        'project': {
            'name': 'Interactive Wand',
            'version': '1.0.0'
        },
        'hardware': {
            'led': {
                'count': hw_config['led_count'],
                'timing': hw_config['led_timing'],
                'spi_device': hw_config['led_spi'],
                'gpio_pin': 19
            },
            'camera': {
                'resolution': [hw_config['camera_width'], hw_config['camera_height']],
                'exposure_time': hw_config['camera_exposure'],
                'analogue_gain': hw_config['camera_gain'],
                'brightness': hw_config['camera_brightness']
            },
            'servo': {
                'enabled': hw_config['servo_enabled'],
                'gpio_pin': hw_config.get('servo_gpio', 12),
                'min_pulse_width': hw_config.get('servo_min_pulse', 0.0005),
                'max_pulse_width': hw_config.get('servo_max_pulse', 0.0025)
            },
            'ir_illuminator': {
                'enabled': hw_config['ir_enabled'],
                'gpio_pin': hw_config.get('ir_gpio', 18),
                'pwm_frequency': hw_config.get('ir_pwm_freq', 1000)
            }
        },
        'detection': {
            'wand_type': hw_config.get('wand_type', 'led'),
            'blob_detector': {
                'min_threshold': detect_config['min_threshold'],
                'max_threshold': detect_config['max_threshold'],
                'min_area': detect_config['min_area'],
                'max_area': detect_config['max_area'],
                'min_circularity': detect_config['min_circularity'],
                'min_inertia_ratio': detect_config['min_inertia']
            },
            'gesture': {
                'presence_duration': detect_config['presence_duration'],
                'stillness_duration': detect_config['stillness_duration'],
                'movement_threshold': detect_config['movement_threshold']
            }
        },
        'audio': {
            'background_volume': audio_config['background_volume'],
            'spell_volume': audio_config['spell_volume']
        },
        'paths': {
            'sounds_dir': 'Sounds',
            'model_file': 'new_custom_classifier.pkl',
            'lastframe_file': 'lastframe.jpg',
            'dataset_dir': 'DatasetCreation'
        }
    }


def show_completion_message():
    """Display success message and next steps"""
    from utils.terminal_ui import Colors

    print(f"\n{Colors.GREEN}{'='*46}{Colors.NC}")
    print(f"{Colors.GREEN}       Setup Complete!{Colors.NC}")
    print(f"{Colors.GREEN}{'='*46}{Colors.NC}")
    print(f"\n{Colors.BOLD}Next steps:{Colors.NC}")
    print(f"  1. {Colors.BLUE}Test your setup:{Colors.NC} python3 test_setup.py")
    print(f"  2. {Colors.BLUE}Train your model:{Colors.NC} cd DatasetCreation && python3 train_spell_classifier.py")
    print(f"  3. {Colors.BLUE}Run the wand tracker:{Colors.NC} python3 harry_potter_wand_cv.py")
    print(f"\n{Colors.GREEN}Happy spell casting!{Colors.NC}\n")
