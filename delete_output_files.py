import shutil
import os

output_directory = "output_files"

# Check if the output directory exists before trying to delete it
if os.path.exists(output_directory):
    # Delete the output folder and its contents
    shutil.rmtree(output_directory)
    print(f"Deleted the '{output_directory}' folder.")
else:
    print(f"The '{output_directory}' folder does not exist.")