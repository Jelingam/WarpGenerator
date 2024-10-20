this tool can be used for generate wirrguard configs for hiddify next app.

current version can be used only on ubuntu and termux in android phone.

base code written in python. only two library are used in this code.

you can install this two library and run this code with this commands.

for termux in android:

```bash
pip install --trusted-host https://pypi.tuna.tsinghua.edu.cn/simple/ tqdm requests
curl https://raw.githubusercontent.com/Jelingam/WarpGenerator/refs/heads/main/wg.py > wg.py && python wg.py
```

for linux:

```bash
sudo apt install python3-requests python3-tqdm
curl https://raw.githubusercontent.com/Jelingam/WarpGenerator/refs/heads/main/wg.py > wg.py && python3 wg.py
```
