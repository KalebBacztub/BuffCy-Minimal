# configure_run.py
import argparse

def configure_run(target_name: str, aslr_mode: str):
    """
    Reads a template and generates a specific docker-compose.run.yml
    with the configuration hardcoded to avoid environment variable issues.
    """
    aslr_value = "2" if aslr_mode == 'on' else "0"
    
    cflags_map = {
        "connmand_no_sec": "-m32 -O2 -fno-stack-protector -z execstack -no-pie",
        "connmand_wdep": "-m32 -O2 -fno-stack-protector -no-pie",
        "connmand_wdep_aslr": "-m32 -O2 -fno-stack-protector -no-pie"
    }
    cflags = cflags_map.get(target_name)
    if not cflags:
        raise ValueError(f"Unknown target name: {target_name}")

    try:
        with open('docker-compose.template.yml', 'r') as f:
            template_content = f.read()
    except FileNotFoundError:
        print("FATAL: docker-compose.template.yml not found.")
        return

    # Replace placeholders with actual values
    content = template_content.replace('%%TARGET_BINARY%%', target_name)
    content = content.replace('%%TARGET_CFLAGS%%', cflags)
    content = content.replace('${ASLR_SETTING}', aslr_value) # Direct replacement

    with open('docker-compose.run.yml', 'w') as f:
        f.write(content)
    
    print(f"✅ Generated 'docker-compose.run.yml' for Target='{target_name}', ASLR='{aslr_mode.upper()}'")
    print("\nReady to run. Use: docker compose -f docker-compose.run.yml up --build")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--target",
        required=True,
        choices=['connmand_no_sec', 'connmand_wdep', 'connmand_wdep_aslr']
    )
    parser.add_argument("--aslr", choices=['on', 'off'], default='on')
    args = parser.parse_args()
    configure_run(args.target, args.aslr)