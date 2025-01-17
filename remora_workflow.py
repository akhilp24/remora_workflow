import subprocess
import os

# Get the current working directory


def main():
    pod5_file = sanitize_path(input("Drag and drop your pod5 file or directory: "))
    can_bam_file = sanitize_path(input("Drag and drop your canonical BAM file: "))
    motif_sequence = input("What is your motif sequence (Ex: TTAGGG): ")
    mod_num = input("Which base is modified (0 represents the first letter): ")
    mod_bam_file = sanitize_path(input("Drag and drop your modified BAM file: "))
    g_type = input("Which G is modified? Enter one of the following (G29, G30, G31): ")

    # Dataset prepare
    subprocess.run([
        "remora", "dataset", "prepare",
        pod5_file, can_bam_file,
        "--output-path", "can_all_chunks",
        "--refine-kmer-level-table", "stationaryfiles/levels.txt",
        "--refine-rough-rescale",
        "--motif", motif_sequence, mod_num,
        "--mod-base-control",
        "--focus-reference-positions", "stationaryfiles/focus_reference_positionscan.bed"
    ])
    subprocess.run([
        "remora", "dataset", "prepare",
        pod5_file, mod_bam_file,
        "--output-path", f"8oxo{g_type}_chunks",
        "--refine-kmer-level-table", "stationaryfiles/levels.txt",
        "--refine-rough-rescale",
        "--motif", motif_sequence, mod_num,
        "--mod-base", "o", "8oxoG",
        "--focus-reference-positions", f"stationaryfiles/focus_reference_positions{g_type}.bed"
    ])

    # Plotting
    plot = input("Would you like to get a plot of your dataset? (y/n) ")
    dataset_plotting(plot, g_type)

    # Training
    trainbool = input("Would you like to train a model? (y/n) ")
    if trainbool == "y":
        print("Great!")
        dataset_configure(g_type)
        dataset_train()
    else:
        print("Got it. No Problem.")


    # Inference
    inferbool = input("Would you like to performance an inference? (y/n)")
    if inferbool == "y":
        best_mod = sanitize_path(input("Input the path of the model you would like to use to perform the inference: "))
        dataset_infer(pod5_dir=pod5_file, can_bam=can_bam_file, mod_bam=mod_bam_file, best_model=best_mod)
    else:
        print("Sounds good.")

def sanitize_path(path):
    current_working_directory = str(os.getcwd())
    print(f"This is the current working directory {current_working_directory}")
    path = path.replace("\\", "/")
    current_working_directory = current_working_directory.replace("\\", "/")
    splitted_cwd = current_working_directory.split("/")
    dirName = splitted_cwd[-1]
    ind = path.index(dirName) + len(dirName) + 1
    fixed_path = "./" + path[ind:]
    fixed_path = fixed_path.replace("\\", "/")
    print(f"This is the fixed path {fixed_path}")
    return fixed_path

def dataset_configure(g_type):
    subprocess.run([
        "remora", "dataset", "make_config",
        "train_dataset.jsn",
        "can_all_chunks",
        f"8oxo{g_type}_chunks",
        "--dataset-weights", "1", "1",
        "--log-filename", "train_dataset.log"
    ])

def dataset_train():
    subprocess.run([
        "remora", "model", "train",
        "train_dataset.jsn",
        "--model", "stationaryfiles/ConvLSTM_w_ref.py",
        "--device", "0",
        "--chunk-context", "50", "50",
        "--output-path", "train_results"
    ])
    print("Congrats!")

def dataset_infer(pod5_dir, can_bam, mod_bam, best_model):
    subprocess.run(["remora", "infer", "from_pod5_and_bam", "--reference_anchored", pod5_dir, can_bam, "--model", best_model, "--out-file", "can_infer.bam", "--log-filename", "can_infer.log", "--device", "0"])
    subprocess.run(["remora", "infer", "from_pod5_and_bam", "--reference_anchored",pod5_dir, mod_bam, "--model", best_model, "--out-file", "mod_infer.bam", "--log-filename", "mod_infer.log", "--device", "0"])

def dataset_plotting(plot, g_type):
    if plot == "y":
        print("Great!")
        can_pod5_file = sanitize_path(input("Drag and drop your canonical pod5 file (Only one file can be used here): "))
        mod_pod5_file = sanitize_path(input("Drag and drop your modified pod5 file (Only one file can be used here): "))
        can_sort_bam_file = sanitize_path(input("Drag and drop your canonical indexed and sorted BAM file (Only one file can be used here): "))
        mod_sort_file = sanitize_path(input("Drag and drop your modified indexed and sorted BAM file (Only one file can be used here): "))
        subprocess.run([
            "remora", "analyze", "plot", "ref_region",
            "--pod5-and-bam", can_pod5_file, can_sort_bam_file,
            "--pod5-and-bam", mod_pod5_file, mod_sort_file,
            "--ref-regions", "stationaryfiles/focus_reference_positionscan.bed",
            "--highlight-ranges", f"stationaryfiles/focus_reference_positions{g_type}.bed",
            "--refine-kmer-level-table", "stationaryfiles/levels.txt",
            "--refine-rough-rescale",
            "--log-filename", "log.txt"
        ])
        print("Finished!")
    else:
        print("Got it. No Problem.")

if __name__ == "__main__":
    main()
