import json
import subprocess
import shlex

def shell_escape(value):
    return shlex.quote(value)

def generate_docker_run(container_name):
    inspect_output = subprocess.check_output(['docker', 'inspect', container_name])
    config = json.loads(inspect_output)[0]

    cmd = ['docker run -d']

    # Name
    cmd.append(f'--name {shell_escape(container_name)}')

    # Environment variables
    env_vars = config['Config'].get('Env', [])
    for env in env_vars:
        cmd.append(f'-e {shell_escape(env)}')

    # Port bindings
    port_bindings = config['HostConfig'].get('PortBindings', {})
    for container_port, host_mappings in port_bindings.items():
        for mapping in host_mappings:
            host_ip = mapping.get('HostIp', '')
            host_port = mapping.get('HostPort', '')
            if host_ip and host_ip != '0.0.0.0':
                port = f'{host_ip}:{host_port}:{container_port}'
            else:
                port = f'{host_port}:{container_port}'
            cmd.append(f'-p {shell_escape(port)}')

    # Volumes
    binds = config['HostConfig'].get('Binds', [])
    for bind in binds:
        cmd.append(f'-v {shell_escape(bind)}')

    # Restart policy
    restart = config['HostConfig'].get('RestartPolicy', {}).get('Name', '')
    if restart and restart != 'no':
        cmd.append(f'--restart {restart}')

    # Working dir
    working_dir = config['Config'].get('WorkingDir', '')
    if working_dir:
        cmd.append(f'-w {shell_escape(working_dir)}')

    # Entrypoint
    entrypoint = config['Config'].get('Entrypoint')
    if entrypoint:
        cmd.append(f'--entrypoint {shell_escape(entrypoint[0])}')

    # Image
    image = config['Config'].get('Image')
    cmd.append(shell_escape(image))

    # Command
    container_cmd = config['Config'].get('Cmd')
    if container_cmd:
        cmd.append(' '.join(shell_escape(arg) for arg in container_cmd))

    return ' \\\n  '.join(cmd)

if __name__ == '__main__':
    import sys
    if len(sys.argv) != 2:
        print("Usage: python docker_run_from_inspect.py <container_name>")
    else:
        print(generate_docker_run(sys.argv[1]))
