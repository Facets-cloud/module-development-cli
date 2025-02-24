import os
import subprocess
import shutil


def run_generate_module(intent, flavor, cloud, title, description):
    """Run the generate-module command using subprocess."""
    command = [
        'ftf', 'generate-module',
        '-i', intent,
        '-f', flavor,
        '-c', cloud,
        '-t', title,
        '-d', description
    ]
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Failed to generate module: {result.stderr}")
    print(result.stdout)
    return result


def run_add_variable(name, type, description, options, path):
    """Run the add-variable command using subprocess."""
    command = [
        'ftf', 'add-variable',
        '-n', name,
        '-t', type,
        '-d', description,
        '--path', path
    ]
    if options:
        command.extend(['--options', options])
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Failed to add variable: {result.stderr}")
    print(result.stdout)
    return result


def test_integration_module_and_variable():
    # Define paths and parameters
    module_path = 'test'
    intent = 'test_intent'
    flavor = 'test_flavor'
    cloud = 'aws'
    title = 'Test Module'
    description = 'A test module'

    # Clean up the module path if it already exists
    if os.path.exists(module_path):
        shutil.rmtree(module_path)

    # Generate the module
    run_generate_module(intent, flavor, cloud, title, description)


    # Combinations of variable types and options
    variables = [
        {'name': 'var1', 'type': 'string', 'description': 'A string variable', 'options': ''},
        {'name': 'var2', 'type': 'number', 'description': 'A number variable', 'options': ''},
        {'name': 'var3', 'type': 'enum', 'description': 'An enum variable with options', 'options': 'opt1,opt2,opt3'},
        {'name': 'var4', 'type': 'object', 'description': 'An object variable', 'options': ''},
        {'name': 'parent.var5', 'type': 'string', 'description': 'A nested var', 'options': ''},
        {'name': 'parent.var5', 'type': 'ee', 'description': 'A nested var', 'options': ''},
    ]

    # Add each variable for full test path
    for var in variables:
        run_add_variable(var['name'], var['type'], var['description'], var['options'], 'test_intent/test_flavor/1.0')


def main():
    test_integration_module_and_variable()


if __name__ == '__main__':
    main()
