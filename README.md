## Setting up your Python Environment

We will use a shared environment to ensure everyone's code runs on everyone else's machine.

1.  **Install Mamba or Miniconda**: If you don't have it, install [Miniforge](https://github.com/conda-forge/miniforge) (recommended) or Anaconda.
2.  **Download the file**: Save `environment.yml` to your project folder.
3.  **Create the environment**:
    Open your terminal (Mac/Linux) or Anaconda Prompt (Windows) and run:
    ```bash
    conda env create -f environment.yml
    ```
4.  **Activate it**:
    ```bash
    conda activate astr502
    ```
5.  **Register it with Jupyter**:
    ```bash
    python -m ipykernel install --user --name=astr502
    ```