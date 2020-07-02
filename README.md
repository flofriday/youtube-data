# youtube-data
Telegram bot and Jupyter Notebook to analyze your YouTube data.

*[Try the bot](https://t.me/youtube_data_bot)*

## Screenshot
![](screenshot.png)

The notebook can do more than just tell you what creators you watch the most, so just try it out.

## Run the bot
### Requirements
1) install docker

### Run it 
```
docker build -t youtubebot-template .
docker run -e TELEGRAM_TOKEN='XXXX' --rm --name youtubebot-container youtubebot-template
```
Replace `XXXX` with your telegram token.

```
docker build -t youtubebot-template .
docker volume create youtubebot-volume
docker run -d --restart unless-stopped \
      -e TELEGRAM_TOKEN='XXXX' \
      --mount type=volume,source=youtubebot-volume,target=/app/data \
      --name youtubebot-container youtubebot-template
```

## Run the jupyter notebook
### Requirements
1) Install jupyter lab [Website](https://jupyter.org/install.html)
2) Add the ipywidgets extension to jupyter lab [Website](https://github.com/jupyter-widgets/ipywidgets#install)
3) Install python libaries used for this notebook `pip install pandas numpy matplotlib ipywidgets`

### Run it 
1) Download your youtube data (and select Format=JSON) [Website](https://takeout.google.com/)
2) Copy the folder "Takeout" into the folder with the Notebook. (Note: I just got a notice that this only works if your language is set to english. If that is not the case you need to modify the path in the first code-cell. This bug will be fixed in the next commits.)
3) Run the notebook with `jupyter lab PATH-TO-NOTEBOOK`
