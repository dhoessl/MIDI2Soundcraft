// Doing some flask socketio

function set_fader(element, value) {
  // get all elements of background css string 
  // add it together with new values
  element.css('background', element.css('background').replace(
    /(.*?)( \d+)(%.*?)( \d+)(%.*?)/,
    "$1 " + value + "$3 " + value + "$5"
  ));
}

function set_config(key, data) {
  if (key == "bpm") {
    const fader_element = $("#delay-bpm");
    const text_element = $("#bpm-value");
    set_fader(fader_element, data);
    set_fader_text(text_element, data);
  } else if (key == "master") {
    console.log(key)
  } else {
    console.log("key: " +key + " not implemented.")
  }
}


window.addEventListener('load', function(){
  // Wait for the Page to fully load and then start the
  // socket io Socket.
  const socket = io()

  socket.on('connect', () => {
    console.log("Connected to server");
  });

  socket.on('init_config', data => {
    console.log("fetched this config");
    console.log(data["msg"]);
  });
});
