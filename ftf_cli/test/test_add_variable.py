from click.testing import CliRunner
from ftf_cli.commands.add_variable import add_variable


def test_add_variable():
    runner = CliRunner()
    result = runner.invoke(add_variable, [
        '--name', 'parent.child',
        '--type', 'string',
        '--description', 'This is a test variable',
        '--path', '/Users/anshulsao/Facets/ai/facets-modules-cli/test/example-intent/example-flavor/1.0'
    ])
    
    print(result.output)
    assert result.exit_code == 0, f"Test failed with result: {result.output}"

    if result.exit_code == 0:
        print('The variable has been added successfully.')


if __name__ == "__main__":
    test_add_variable()
