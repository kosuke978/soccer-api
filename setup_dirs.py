"""Directory structure setup script."""
import os

# Create tests directory structure
tests_dir = "tests"
if not os.path.exists(tests_dir):
    os.makedirs(tests_dir)
    print(f"Created {tests_dir} directory")

# Create __init__.py in tests
init_file = os.path.join(tests_dir, "__init__.py")
if not os.path.exists(init_file):
    open(init_file, 'w').close()
    print(f"Created {init_file}")

print("Directory structure setup complete!")
