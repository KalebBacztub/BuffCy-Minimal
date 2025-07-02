# configure_run.py
import argparse
import subprocess

def set_aslr(aslr_mode: str):
    aslr_value = "0" if aslr_mode == 'off' else "2"
    print(f"[CONFIG] Setting ASLR to {aslr_value}...")
    try:
        subprocess.run(
            ["sysctl", "-w", f"kernel.randomize_va_space={aslr_value}"],
            check=True,
            capture_output=True
        )
        print(f"[CONFIG] ASLR set successfully.")
    except Exception as e:
        print(f"FATAL: Failed to set ASLR. Run this script with 'sudo'. Error: {e}")
        exit(1)

def configure_run(target_name: str, aslr_mode: str):
    set_aslr(aslr_mode)
    
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

    content = template_content.replace('%%TARGET_BINARY%%', target_name)
    content = content.replace('%%TARGET_CFLAGS%%', cflags)

    with open('docker-compose.run.yml', 'w') as f:
        f.write(content)
    
    print(f"✅ Generated 'docker-compose.run.yml' for Target='{target_name}'")
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