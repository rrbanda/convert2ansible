# Automation Code SorcererX

A small expandable Python application that utilises either [IBM Watsonx.ai Runtime](https://cloud.ibm.com/catalog/services/watsonxai-runtime) or [Ollama](https://ollama.com) locally to convert [Puppet](https://www.puppet.com) Modules or [Chef](https://www.chef.io) Recipes to [Ansible](https://www.redhat.com/en/ansible-collaborative) Playbooks.  

Some sample results are included to compare the different modles from Watsonx.ai and Ollama.

![architecture](https://github.com/bpaskin/Automation-Code-SorcererX/blob/main/images/code-sorcererx.png)

---

### To Use: ###

This was test with Python 3.12

1. Clone the code to your local system 
```
git clone https://github.com/bpaskin/Automation-Code-SorcererX.git
```
2. Enter the directory
```
cd Automation-Code-SorcererX
```
3. Create and run in a virtual environment
```
python -m venv venv
source venv/bin/activate
```
4. Add the required modules
```
pip install -r requirements.txt
````
5. Edit the settings file and update the settings to your environment (ai_to_use is either wxai or ollama)
```
vi settings.config
```
6. Add your Pupper or Chef files to the `upload` directory
7. Run the program
```
python __main__.py
```
8. Evaluate the results in the directory specified in the settings.config
</br>
</br>
𐕣 Funeral Winter 𐕣
