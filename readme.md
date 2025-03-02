# Splitter

## Overview
Splitter is a tool designed to split large files into smaller chunks for easier handling and processing. It supports various file formats and provides options for customizing the size and number of chunks.

## Features
- Split large files into smaller chunks
- Support for multiple file formats (e.g., text, CSV, JSON)
- Customizable chunk size and number of chunks
- Easy to use command-line interface

## Installation
To install Splitter, clone the repository and install the required dependencies:

```bash
git clone https://github.com/yourusername/splitter.git
cd splitter
pip install -r requirements.txt
```

## Usage
To use Splitter, run the following command:

```bash
python splitter.py --input <input_file> --output <output_directory> --size <chunk_size>
```

### Arguments
- `--input`: Path to the input file to be split
- `--output`: Directory where the output chunks will be saved
- `--size`: Size of each chunk (e.g., 10MB, 1000 lines)

## Examples
Split a text file into chunks of 10MB each:

```bash
python splitter.py --input largefile.txt --output chunks/ --size 10MB
```

Split a CSV file into chunks of 1000 lines each:

```bash
python splitter.py --input data.csv --output chunks/ --size 1000
```

## Contributing
Contributions are welcome! Please fork the repository and submit a pull request.

## License
This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Contact
For any questions or feedback, please contact [yourname@example.com](mailto:yourname@example.com).
