"""
Test script to verify file saving functionality
"""
import os
import uuid

# Get the directory where the files should be saved
module_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(module_dir, "src", "deep_research_from_scratch")
files_dir = os.path.join(src_dir, "files")

print(f"Module directory: {module_dir}")
print(f"Source directory: {src_dir}")
print(f"Files directory: {files_dir}")
print(f"Files directory exists: {os.path.exists(files_dir)}")

# Create the files directory if it doesn't exist
os.makedirs(files_dir, exist_ok=True)

# Generate a unique filename using UUID
report_id = str(uuid.uuid4())
filename = f"test_report_{report_id}.md"
filepath = os.path.join(files_dir, filename)

# Save a test report
test_content = "# Test Report\n\nThis is a test to verify file saving works correctly."
with open(filepath, "w", encoding="utf-8") as f:
    f.write(test_content)

print(f"\nTest report saved to: {filepath}")
print(f"File exists: {os.path.exists(filepath)}")

# List all files in the directory
print(f"\nFiles in {files_dir}:")
for file in os.listdir(files_dir):
    print(f"  - {file}")
