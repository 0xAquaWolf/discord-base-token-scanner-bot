import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

def add_numbers(a, b):
    logging.debug(f"Adding {a} and {b}")
    return a + b

def divide_numbers(a, b):
    logging.debug(f"Dividing {a} by {b}")
    if b == 0:
        logging.error("Division by zero!")
        return None
    return a / b

def main():
    logging.info("Starting the program")
    
    result1 = add_numbers(5, 3)
    logging.info(f"Result of addition: {result1}")
    
    result2 = divide_numbers(10, 2)
    logging.info(f"Result of division: {result2}")
    
    result3 = divide_numbers(8, 0)
    logging.info(f"Result of division by zero: {result3}")
    
    logging.info("Ending the program")

if __name__ == "__main__":
    main()