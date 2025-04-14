# import argparse
# import sys
# sys.path.append('.')
# from macosagent.macosagent import create_agent
# # from dotenv import load_dotenv
# import weave
# # load the environment variables from .env file
# from dotenv import load_dotenv
# load_dotenv()

# weave.init("Macosagent")
# @weave.op()
# def main():
#     parser = argparse.ArgumentParser()
#     parser.add_argument(
#         "--prompt", 
 
#         default=" Search for the price of 3 pairs of sports shoes from 'Nike ReactX Rejuven8', 'Li Ning wade shadow 6' and 'Adidas Unisex Adult Daily 4.0 Sneaker', and insert the price and product name into the corresponding location of Excel './cache/Shoes Price Statistics.xlsx'.")
#     args = parser.parse_args()
#     agent = create_agent()
#     result = agent.run(args.prompt)
#     # agent.save_trajectory()
#     print("Agent Response:", result)

# if __name__ == "__main__":
#     main()

# from powerpoint_agent import PowerPointAgent
from wechat_agent import WechatAgent