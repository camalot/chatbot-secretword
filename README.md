# CHATBOT TWITCH TEAM

A script that will automatically shoutout a streamer from the specified twitch team.


## REQUIREMENTS

- Install [StreamLabs Chatbot](https://streamlabs.com/chatbot)
- [Enable Scripts in StreamLabs Chatbot](https://github.com/StreamlabsSupport/Streamlabs-Chatbot/wiki/Prepare-&-Import-Scripts)
- [Microsoft .NET Framework 4.7.2 Runtime](https://dotnet.microsoft.com/download/dotnet-framework/net472) or later

## INSTALL

- Download the latest zip file from [Releases](https://github.com/camalot/chatbot-shoutout/releases/latest)
- Right-click on the downloaded zip file and choose `Properties`
- Click on `Unblock`  
[![](https://i.imgur.com/vehSSn7l.png)](https://i.imgur.com/vehSSn7.png)  
  > **NOTE:** If you do not see `Unblock`, the file is already unblocked.
- In Chatbot, Click on the import icon on the scripts tab.  
  ![](https://i.imgur.com/16JjCvR.png)
- Select the downloaded zip file
- Right click on `Twitch Team` row and select `Insert API Key`. Click yes on the dialog.  
[![](https://i.imgur.com/AWmtHKFl.png)](https://i.imgur.com/AWmtHKF.png)  

## CONFIGURATION

Make sure the script is enabled  
[![](https://i.imgur.com/d8rAJN9l.png)](https://i.imgur.com/d8rAJN9.png)  

Click on the script in the list to bring up the configuration.

### GENERAL SETTINGS  

[![](https://i.imgur.com/o0UnLw4l.png)](https://i.imgur.com/o0UnLw4.png)  

| ITEM | DESCRIPTION | DEFAULT | 
| ---- | ----------- | ------- | 
| `Stream Team Name` | The stream team `id` for the `twitch.tv/team/<id>` | `` |  
| `Host Message Template` | The stream team `id` for the `twitch.tv/team/<id>` | `` |  
| `Raid Message Template` | The stream team `id` for the `twitch.tv/team/<id>` | `` |  

> **The default for the templates:**
>
> ```
> Fellow $stream_team streamer @$display_name has raided the channel. Make sure you go give them a follow https://twitch.tv/$name
> ```
> Template Variables:
> - `$name`: The name of the person raiding/hosting
> - `$display_name`: The display name of the person
> - `$stream_team`: The name of the stream team
> - `$action`: The action performed. `hosted` or `raided`


### API KEYS (REQUIRED)

[![](https://i.imgur.com/7VMWSyXl.png)](https://i.imgur.com/7VMWSyX.png)  

| ITEM | DESCRIPTION | DEFAULT | 
| ---- | ----------- | ------- | 
| `Streamlabs Socket Token` | Your streamlabs socket token. | `` |  
| `Get Your Socket Token Here` | Opens the page to get the token | `` |
| `Twitch Client-ID` | Your Twitch Client-ID. | `` |  
| `Get Your Twitch Client-ID Here` | Opens the page to create an app to create a client id. | `` |


To Create a Twitch Client ID fill out the form like the following:

[![](https://i.imgur.com/R3VD0D8l.png)](https://i.imgur.com/R3VD0D8.png)  



### INFORMATION  

[![](https://i.imgur.com/MKxaCXLl.png)](https://i.imgur.com/MKxaCXL.png)  

| ITEM | DESCRIPTION | 
| ---- | ----------- | 
| `Donate` | If you feel like supporting, you can click this |  
| `Follow Me On Twitch` | You can follow me on twitch. |  
| `Open Readme` | Opens this document |  
| `Check for Updates` | Updates this script. |  
| `Save Settings` | Save the settings. |  
