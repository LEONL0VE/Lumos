# Lumos
[![DOI:10.1109/TVCG.2021.3114827](https://zenodo.org/badge/DOI/10.1109/TVCG.2021.3114827.svg)](https://doi.org/10.1109/TVCG.2021.3114827)

Lumos is a visual data analysis tool that captures and shows the interaction history with data to increase awareness of such analytic behaviors. Using in-situ (at the place of interaction) and ex-situ (in an external view) visualization techniques, Lumos provides real-time feedback to users for them to reflect on their activities. For example, Lumos highlights datapoints that have been previously examined in the same visualization (in-situ) and also overlays them on the underlying data distribution (i.e., baseline distribution) in a separate visualization (ex-situ).

This codebase comprises an easy-to-extend <a href="https://angular.io/" target="_blank">Angular</a> frontend and a <a target="_blank" href="https://www.python.org/downloads/release/python-310/">Python 3.10</a>, <a target="_blank" href="https://socket.io/">SocketIO</a>, <a target="_blank" href="https://docs.aiohttp.org/en/stable/">AIOHTTP</a> backend with an API for real-time bi-directional communication with the frontend over the HTTP REST and websocket protocols.


## Setup
Instructions can be found in the following sub-directories:
- [app](app) (frontend)
- [server](server) (backend)



## Credits
Lumos was created by <a target="_blank" href="http://narechania.com">Arpit Narechania</a>, Adam Coscia, Emily Wall, and Alex Endert.


### Citation
```bibTeX
@article{narechania2022lumos,
  author={Narechania, Arpit and Coscia, Adam and Wall, Emily and Endert, Alex},
  journal={{IEEE Transactions on Visualization and Computer Graphics}}, 
  title={{Lumos: Increasing Awareness of Analytic Behavior during Visual Data Analysis}}, 
  year={2022},
  volume={28},
  number={1},
  pages={1009-1018},
  doi={10.1109/TVCG.2021.3114827}
}
```

## Deploy on Render
- Build `app` repository code from inside that repository: `ng build`
    - This should add/update contents inside the `server/public` folder.
- Add, commit code via git.
- Push to main branch.
- Set PYTHON_VERSION=3.10.21 as Environment Variable in Render
- Try `https://lumos-1stu.onrender.com` in browser (there may be a 30s wait time because we are using the Free tier, and hence, the server can be idle)
 
## Deploy on Heroku (now Sunset as it was expensive to maintain)
- Build `app` repository code from inside that repository: `ng build`
    - This should add/update contents inside the `server/public` folder.
- Verify `Procfile` inside the `server` folder.
- `heroku login`
- If not added, add git remote: `git remote add heroku https://git.heroku.com/lumos-webapp.git`
- Set buildpack for this project: `heroku buildpacks:set heroku/python` (it might err that the buildpack is already set on your app. Good, nothing to worry then.)
- Add, commit code via git.
- Push only the `server` folder as a subtree (run it from the toplevel of the working tree): `git subtree push --prefix server heroku main`
- Hope!
- Try `https://lumos-webapp-4aeadb3bf30d.herokuapp.com` in browser.
- Check logs via `heroku logs --tail`
- Restart via `heroku restart --app lumos-webapp`


## License
The software is available under the [MIT License](https://github.com/lumos-vis/lumos/blob/master/LICENSE).


## Contact
If you have any questions, feel free to [open an issue](https://github.com/lumos-vis/lumos/issues/new/choose) or contact [Arpit Narechania](https://narechania.com).
