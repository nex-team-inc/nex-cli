import os

import click

def find_android_sdk():
    """
    Find the Android SDK directory.
    """
    if os.environ.get('ANDROID_HOME'):
        sdk = os.environ.get('ANDROID_HOME')
    elif os.environ.get('ANDROID_SDK_ROOT'):
        sdk = os.environ.get('ANDROID_SDK_ROOT')
    elif os.environ.get('ANDROID_SDK'):
        sdk = os.environ.get('ANDROID_SDK')
    elif os.environ.get('ANDROID_SDK_HOME'):
        sdk = os.environ.get('ANDROID_SDK_HOME')
    elif os.environ.get('ANDROID_SDK_DIR'):
        sdk = os.environ.get('ANDROID_SDK_DIR')
    elif os.environ.get('ANDROID_SDK_PATH'):
        sdk = os.environ.get('ANDROID_SDK_PATH')
    else:
        sdk = "~/Library/Android/sdk"

    sdk = os.path.expanduser(sdk)

    if not os.path.isdir(sdk):
        raise click.ClickException(f'Android SDK not found at {sdk}')

    return sdk

def find_android_build_tools():
    """
    Find the Android build tools directory.
    """
    sdk = find_android_sdk()
    build_tools = os.path.join(sdk, 'build-tools')

    if not os.path.isdir(build_tools):
        raise click.ClickException(f'Android build tools not found at {build_tools}')

    # Get the latest version of the build tools
    dirs = os.listdir(build_tools)
    if len(dirs) == 0:
        raise click.ClickException(f'No build tools found at {build_tools}')
    dirs.sort(reverse=True)
    return os.path.join(build_tools, dirs[0])
