//var apiDomain = 'https://doarama-thirdparty-dev.herokuapp.com';
var apiDomain = 'https://api.doarama.com';

var playerLoaded = new $.Deferred();
var playerApiReady = new $.Deferred();
var playerReady = new $.Deferred();
var player;

function wrapPost(method, value) {
  var msg = {
    "method" : method,
    "value" : value
  };
  // Only allow posting messages once API is ready
  $.when(playerLoaded, playerApiReady).then(function(player) {
    console.log("posting: " + JSON.stringify(msg));
    player.postMessage(msg, apiDomain);
  });
}

document.getElementById('doarama-iframe').onload = function() {
  // Access the iframe's content window
  player = document.getElementById('doarama-iframe').contentWindow;

  console.log('iframe has loaded!');
  playerLoaded.resolve(player);
};

// Receive messages from the API
function onMessageReceived(e) {

  if (e.data.method === 'ready') {
    console.log('Player is ready and all tracks loaded!');
    playerReady.resolve();

  } else if (e.data.method === 'api-ready') {
    console.log('API is ready!');
    playerApiReady.resolve();

  } else {
    console.log('client received: ' + JSON.stringify(e.data));
  }
}

// We can do some initial UI visibility configuration before tracks have loaded
// NOTE: Only visibility configuration is to be done before playerReady has resolved
wrapPost('setChartVisibility', false);
wrapPost('setStatsVisibility', true);

window.addEventListener('message', onMessageReceived, false);

// TWB: Configure doarama the way I like
  // Posting messages once API is ready
  $.when(playerLoaded, playerApiReady).then(function(player) {
wrapPost('setTrailLength', 10);
wrapPost('setPlaybackRate',1.5);
wrapPost('setViewDistance', 25);
  });


