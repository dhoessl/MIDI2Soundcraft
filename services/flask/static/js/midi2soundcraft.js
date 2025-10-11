// Doing some flask socketio

function set_fader_mute (element) {
  el
}

function set_fader(element, value) {
  // get all elements of background css string 
  // add it together with new values
  element.css('background', element.css('background').replace(
    /(.*?)( \d+(\.\d+|))(%.*?)( \d+(\.\d+|))(%.*?)/,
    "$1 " + value + "$4 " + value + "$7"
  ));
}

function set_fader_text(element, text) {
  element.text(text);
}

function set_mute(btn, mix, req_state) {
  if (req_state && btn.hasClass("btn-outline-secondary")){
    // if req_state and btn is not mute then mute it
    btn.removeClass("btn-outline-secondary").addClass("btn-outline-danger");
  } else if (!req_state && btn.hasClass("btn-outline-danger")) {
    // if not req_state and btn has the mute class
    btn.removeClass("btn-outline-danger").addClass("btn-outline-secondary");
  }
  if (req_state && mix.css("background").includes("rgb(0, 128, 0)")) {
    mix.css(
      "background",
      mix.css("background").replace("rgb(0, 128, 0)", "rgb(255, 0, 0)")
    );
  } else if (!req_state && mix.css("background").includes("rgb(255, 0, 0)")) {
    mix.css(
      "background",
      mix.css("background").replace("rgb(255, 0, 0)", "rgb(0, 128, 0)")
    );
  }
}

function set_active_view(btn) {
  $('button[id^=view]').each(function() {
    if ($(this).hasClass("btn-outline-success")){
      $(this).removeClass("btn-outline-success").addClass("btn-outline-secondary");
    }
    if ($(this).is(btn)) {
      $(this).removeClass("btn-outline-secondary");
      $(this).removeClass("btn-outline-danger");
      $(this).addClass("btn-outline-success");
    }
  });
  if (!btn.is($("#view7"))) {
    $("#view7").removeClass("btn-outline-danger").addClass("btn-outline-danger");
  }
}

function set_shift(btn, state) {
  if (state && !btn.hasClass("btn-outline-warning")) {
    btn.removeClass("btn-outline-secondary").addClass("btn-outline-warning");
    if (btn.is($("#midimix-shift"))) {
      // midimix display
      return true;
    } else {
      // apc display
      $('span[id ^=lowerbtn]').each(function() {
        $(this).text("None");
      });
      $("#lowerbtn4text").text("Mix +");
      $("#lowerbtn4").removeClass("btn-outline-secondary").addClass("btn-outline-warning");
      $("#lowerbtn5text").text("Mix -");
      $("#lowerbtn5").removeClass("btn-outline-secondary").addClass("btn-outline-warning");
      $("#lowerbtn6text").text("CH <");
      $("#lowerbtn6").removeClass("btn-outline-secondary").addClass("btn-outline-warning");
      $("#lowerbtn7text").text("CH >");
      $("#lowerbtn7").removeClass("btn-outline-secondary").addClass("btn-outline-warning");
    }
  } else if (!state && btn.hasClass("btn-outline-warning")) {
    btn.removeClass("btn-outline-warning").addClass("btn-outline-secondary");
    if (btn.is($("#midimix-shift"))) {
      // midimix display
      return true;
    } else {
      // apc display
      $('span[id ^=lowerbtn]').each(function() {
        $(this).text("Mute");
      });
    }
  }
}

function update_dials(data) {
  $("div.midi-dial").each(function() {
    channel_fx = $(this).attr("id").match(/fx(\d)channel(\d+)/);
    set_fader($(this), data[channel_fx[2]][channel_fx[1]]["value"]);
    set_fader_text($("#" + channel_fx[0] + "text"), data[channel_fx[2]][channel_fx[1]]["text"]);
  });
}

function set_config(key, data) {
  if (key == "bpm") {
    const fader_element = $("#delay-bpm");
    const text_element = $("#bpm-value");
    set_fader(fader_element, data["bpm"] - 60);
    set_fader_text(text_element, data["bpm"]);
  } else if (key == "master") {
    const mix_element = $("#channel7mix");
    const text_element = $("#channel7value");
    set_fader(mix_element, data["percent"]);
    set_fader_text(text_element, data["text"]);
  } else if (key == "channel_fx") {
    const fader_element = $("#fx" + data["fx"] + "channel" + data["channel"]);
    const text_element = $("#fx" + data["fx"] + "channel" + data["channel"] + "text");
    set_fader(fader_element, data["percent"]);
    set_fader_text(text_element, data["text"]);
  } else if (key == "channel_mix") {
    const mix_element = $("#channel" + data["channel"] + "mix");
    const text_element = $("#channel" + data["channel"] + "value");
    if (mix_element.length > 0) {
      set_fader(mix_element, data["percent"]);
    }
    if (text_element.length > 0) {
      set_fader_text(text_element, data["text"]);
    }
  } else if (key == "channel_mute") {
    const btn_element = $("#lowerbtn" + data["channel"]);
    const mix_element = $("#channel" + data["channel"] + "mix");
    if (btn_element.length > 0){
      set_mute(btn_element, mix_element, data["mute_state"]);
    }
  } else if (key == "return_fx") {
    const mix_element = $("#channel" + data["channel"] + "mix");
    const text_element = $("#channel" + data["channel"] + "value");
    set_fader(mix_element, data["percent"]);
    set_fader_text(text_element, data["text"]);
  } else if (key == "toggle_apc_side") {
    const btn_element = $("#view" + data["button"]);
    set_active_view(btn_element);
  } else if (key == "shift") {
    if (data["controller"] == "apc") {
      const btn_element = $("#shift");
    } else if (data["controller"] == "midimix") {
      const btn_element = $("#midimix-shift");
    }
    set_shift(btn_element, data["state"]);
  } else if (key == "fx_params") {
    const fader_element = $("#fx" + data["fx"] + data["param"]);
    const text_element = $("#fx" + data["fx"] + data["param"] + "value");
    set_fader(fader_element, data["percent"]);
    set_fader_text(text_element, data["text"]);
  } else if (key == "channel_dials") {
    update_dials(data);
  } else {
    console.log("key: " +key + " not implemented.");
  }
}


window.addEventListener('load', function(){
  // Wait for the Page to fully load and then start the
  // socket io Socket.
  const socket = io()

  socket.on('connect', () => {
    console.log("Connected to server");
  });

  socket.on("config_update", data => {
    console.log("Update config! key: " + data["key"]);
    set_config(data["key"], data["data"]);
  });
});
