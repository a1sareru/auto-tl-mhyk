import argparse
import yaml
import os


def load_replacements(config_path='replace.yml'):
    config_path = os.path.join(os.path.dirname(__file__), 'replace.yml')
    print(f"Loading replacements from: {config_path}")
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def replace_text(text, replacements):
    for src, dst in replacements.items():
        text = text.replace(src, dst)
    return text


def main():
    parser = argparse.ArgumentParser(description="Replace terms in a file based on replace.yml.")
    parser.add_argument('--input', required=True, help="Path to the input text file.")
    args = parser.parse_args()

    input_path = args.input
    if not os.path.isfile(input_path):
        print(f"Input file not found: {input_path}")
        return

    with open(input_path, 'r', encoding='utf-8') as f:
        content = f.read()

    replacements = load_replacements()
    new_content = replace_text(content, replacements)

    base, ext = os.path.splitext(input_path)
    output_path = f"{base}-new{ext}"

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(new_content)

    print(f"Replaced content written to: {output_path}")


if __name__ == '__main__':
    main()