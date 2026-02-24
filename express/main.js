import e from "express";
import fs from "fs";
import axios from "axios";
import { config } from "dotenv";
import { getBase64EncodedCredentials } from "./utils.js";

config(); //dot env config load

const client_id = process.env.CLIENT_ID;
const client_secret = process.env.CLIENT_SECRET;

const base64EncodedCredentials = getBase64EncodedCredentials(client_id, client_secret)

const redirect_uri = "http://127.0.0.1:8080/callback";

const app = e(); //express app

app.get("/login", function (req, res) {
  const state = process.env.SPOTIFY_STATE;
  const scope = "user-read-private user-read-email user-read-playback-state";
  res.redirect(
    `https://accounts.spotify.com/authorize?response_type=code&client_id=${client_id}&scope=${scope}&redirect_uri=${redirect_uri}&state=${state}`,
  );
});

app.get("/callback", async (req, res) => { //callback function which spotify redirects to
  const {code} = req.query;
  if (code) {
    fs.writeFileSync("auth_code.txt", code);

    try {
      const auth_res = await axios.post(
        "https://accounts.spotify.com/api/token",
        {
          grant_type: "authorization_code",
          code,
          redirect_uri,
        },
        {
          headers: {
            Authorization: `Basic ${base64EncodedCredentials}`,
            "Content-Type": "application/x-www-form-urlencoded",
          },
        },
      );

      const { data } = auth_res;
      console.log(data);

      const access_code  = data.access_token;

      const playing_res = await axios.get(
        "https://api.spotify.com/v1/me/player/currently-playing",
        {
          headers: {
            Authorization: `Bearer ${access_code}`,
          },
        },
      );

      console.log(playing_res.data);

      res.json({
        spotify_track_url: playing_res.data.item.external_urls.spotify,
      });

      return;
    } catch (error) {
      // console.error(error);
      res.send(error);
      return;
    }

    res.send(
      "<h1>✅ Login Successful!</h1><p>You can close this window and return to the app.</p>",
    );
  } else {
    res.send("<h1>❌ Login Failed</h1><p>No authorization code received.</p>");
  }
});

app.listen(8080);
