import os

def delete_project_files(project_path):
    files_to_delete = [
        "current_sample_training.csv",
        "epoch_training.json",
        "metrics.json",
        "labels.db",
        "hilts/hilts_sample.json",
        "hilts_data.csv",
        "loop.txt",
    ]

    for file_name in files_to_delete:
        file_path = os.path.join(project_path, file_name)
        if os.path.exists(file_path):
            if os.path.isdir(file_path):
                # Remove directory
                import shutil
                shutil.rmtree(file_path)
                print(f"Deleted directory: {file_path}")
            else:
                # Remove file
                os.remove(file_path)
                print(f"Deleted file: {file_path}")
        else:
            print(f"File or directory does not exist: {file_path}")

if __name__ == "__main__":
    # Replace 'your_project_path' with the actual project path
    # project_path = input("Enter the project path: ").strip()
    project_path = "data/demo"  # Example path
    delete_project_files(project_path)
