
from word_agent import WordAgent 

news_content = """                                                                                              
Date: September 15, 2024                                                                                        
Location: Trump International Golf Club, West Palm Beach, Florida                                               
Target: Donald Trump                                                                                            
Description: An alleged assassination attempt on Donald Trump occurred at his golf club when suspect Ryan       
Wesley Routh was seen aiming a rifle at a Secret Service agent.                                                 
Weapon: SKS-style rifle                                                                                         
Result: No injuries reported; one suspect arrested                                                              
Suspect: Ryan Wesley Routh, 58, Hawaii resident, previously lived in Greensboro, North Carolina                 
Political Activity: History of political activity, formerly supported Trump, became disillusioned               
Criminal History: Prior conviction for possessing a fully automatic weapon, over 100 criminal counts including  
driving violations and possession of stolen items                                                               
Charges: Attempted assassination of a presidential candidate, Assaulting a federal officer, Criminal            
possession of a firearm (3 counts), Attempted felony murder                                                     
""" 

instructions =  f"Open the document './cache/2024TrumpAssassination.docx', navigate to Chapter 3, insert the following content: {news_content}"
agent = WordAgent()
result = agent.forward(instructions)
print(result)