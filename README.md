# SFM Discord RPC

This repository contains the SFM Discord RPC project. SFM Discord RPC is a tool that allows you to display your current Source Filmmaker (SFM) session information as a rich presence on Discord. It enhances your Discord status by showing the current SFM map and the time spent working on your SFM project.
I want to credit https://github.com/niveshbirangal/discord-rpc for coding the connection between Discord and Python 3, I had to rewrite for compatibility 
with python 2.7.6, but my life was made easier thanks to his efforts.

Source Filmmaker Discord Rich Presence script
Installation avaliable on workshop page 

https://steamcommunity.com/sharedfiles/filedetails/?id=2717645611

## Features

- **Display SFM session information**: SFM Discord RPC updates your Discord status to show the SFM map you are currently working on.
- **Track session duration**: It tracks the time you spend working on your SFM project and displays it on Discord.
- **Customizable presence**: You can customize the presence message to include additional information or customize the appearance.

## Installation

To use SFM Discord RPC, follow these steps:

1. Download the latest release from the [Releases](https://github.com/valance1/sfm-discord-rpc/releases) page.
2. Extract the downloaded archive to a location of your choice.
3. Run the `SFM-Discord-RPC.exe` executable.
4. SFM Discord RPC will automatically detect your SFM session and update your Discord status accordingly.

Please note that SFM Discord RPC requires Discord to be running on your computer for it to work properly.

## Configuration

By default, SFM Discord RPC uses the SFM installation path obtained from the Windows registry. If you have a different SFM installation path or want to customize the presence message, you can modify the `config.json` file located in the installation directory.

Open the `config.json` file in a text editor and modify the values as needed:

- `sfmPath`: The path to your SFM installation directory (e.g., `"C:\\Program Files (x86)\\Steam\\steamapps\\common\\SourceFilmmaker"`).
- `presenceMessage`: The presence message displayed on Discord. You can use the following placeholders: `{map}` for the SFM map name and `{time}` for the session duration.

Save the `config.json` file after making your changes, and SFM Discord RPC will use the updated configuration on the next launch.

## Contributing

Contributions to SFM Discord RPC are welcome! If you want to contribute, please follow these steps:

1. Fork this repository and clone it to your local machine.
2. Make your changes and test them thoroughly.
3. Commit your changes with a descriptive commit message.
4. Push your changes to your forked repository.
5. Open a pull request in this repository, explaining your changes and their purpose.

Please ensure that your contributions align with the code style and standards used in this project.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for more information.

## Contact

If you have any questions or suggestions regarding SFM Discord RPC, feel free to reach out:
- GitHub: [valance1](https://github.com/valance1)


