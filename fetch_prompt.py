from datasets import load_dataset
import json

# Load the dataset
dataset = load_dataset("k-mktr/improved-flux-prompts-photoreal-portrait", split="train")
# Change to below if you wanna fetch all dataset.
# selected_dataset = dataset 
selected_dataset = dataset.select(range(20))

def save_training_data(data: list, output_file="simple_prompts.json"):
    """
    Save training data to a JSON file.
    
    Args:
        data (list): List of training data entries where each entry is a dictionary.
        output_file (str): Path to output JSON file.
    """
    # Create a wrapper object with a "prompts" key containing the array of prompts
    output_data = {"prompts": data}
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    # Prepare the prompts
    prompts = selected_dataset['prompt']
    structured_data = [{"prompt": text} for text in prompts]
    save_training_data(structured_data)