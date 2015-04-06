var INPUT_DISTANCE = 400;

var scene, camera, renderer, controls, pointer, vObj;

var cells = [];

var move = {
  up: false,
  down: false
};

// current element under pointer
var currentIndex = false;

function init () {
  // create scene
  scene = new THREE.Scene();

  // add renderer
  renderer = new THREE.CSS3DStereoRenderer();
  renderer.setSize( window.innerWidth, window.innerHeight );
  renderer.domElement.style.position = 'absolute';
  document.body.appendChild( renderer.domElement );

  // add lighting
  scene.add( new THREE.AmbientLight( 0x666666 ) );
  light = new THREE.PointLight( 0xaaddaa, .5 );
  light.position.set( 50, 1200, -500 );
  scene.add( light );

  // add camera
  camera = new THREE.PerspectiveCamera( 40, window.innerWidth /
      window.innerHeight, 1, 1000 );

  scene.add( camera );

  // add view controls
  controls = new THREE.DeviceOrientationControls( camera );

  // add pointer / pointer for camera

  var domElem = document.createElement( 'div' );
  domElem.className = 'pointer';
  domElem.style.width = window.innerWidth * 0.01 + 'px';
  domElem.style.height = window.innerWidth * 0.01 + 'px';

  pointer = new THREE.CSS3DObject( domElem );
  pointer.position.set( 0, 0, -300 );

  camera.add( pointer );

  // add cells
  makeCells(24, 4);
  animate();

  // addVideoFeed();
  initGyro();
}

function findFocusedCell () {
  var p = pointer.elementL.getBoundingClientRect(),
    elem = document.elementFromPoint(p.left, p.top),
    prevIndex,
    cell, oldObj, currentObj;

  // if element is cell
  if (elem && elem.className.indexOf("cell") >= 0) {

    // check for last hovered cell
    if (currentIndex) {
      prevIndex = currentIndex;
      oldObj = cells[ prevIndex ];

    } else {
      prevIndex = false;
    }

    currentIndex = elem.getAttribute("data-index");
    currentObj = cells[ currentIndex ];

    // if element has changed
    if (prevIndex && prevIndex !== currentIndex) {

      // remove focus from previously focused elements
      oldObj.elementL.className =
          oldObj.elementL.className.replace("focused", "");

      oldObj.elementR.className =
          oldObj.elementR.className.replace("focused", "");

      // console.log(currentObj);
      // add focus to new elements
      currentObj.elementL.focus();
      currentObj.elementL.className += " focused";
      currentObj.elementR.className += " focused";
    }

    // sync left and right elements values
    currentObj.elementR.value = currentObj.elementL.value;

  } else {

    if (currentIndex) {
      prevIndex = currentIndex;
      oldObj = cells[ prevIndex ];

      oldObj.elementL.className =
          oldObj.elementL.className.replace("focused", "");

      oldObj.elementR.className =
          oldObj.elementR.className.replace("focused", "");
    }
    currentIndex = false;
  }
}

function makeCells (numCells, numCols) {
  var angle = (2 * Math.PI) / numCells,
    elemWidth = 2 * INPUT_DISTANCE * Math.tan(angle / 2),
    cAngle = 0;

  var pos = {
    x: camera.position.x + INPUT_DISTANCE,
    z: camera.position.z
  }

  var geometry = new THREE.PlaneGeometry(5, 5);

  var material = new THREE.MeshBasicMaterial({ wireframe: true });

  var yCoord = camera.position.z;
  var centerPoint = new THREE.Vector3(0,0,1);

  var index;

  for (var i = 0; i <= numCells; i++) {

    for (var j = 0; j < numCols; j++) {
      index = j + (i * numCols);

      cells[index] = makeCell(index, elemWidth, elemWidth);

      // * 1.1 to remove overlap. need to find out what causes overlap
      yCoord = j * elemWidth * 1.1;

      // position.set(x, y, z)
      cells[index].position.set(
        pos.x,
        yCoord,
        pos.z
      );

      scene.add(cells[index]);

      centerPoint.setY(yCoord);

      cells[index].lookAt(centerPoint);
    }
    pos.x = camera.position.x + (INPUT_DISTANCE * Math.cos(cAngle));
    pos.z = camera.position.z + (INPUT_DISTANCE * Math.sin(cAngle));

    cAngle += angle;
  }
  camera.position.y = (j / 2) * elemWidth * 1.1
}

// change to more OO approach, cell constructor
function makeCell (cellIndex, width, height) {
  var cell = document.createElement( 'textarea' );

  cell.className = 'cell';
  cell.setAttribute("data-index", cellIndex);

  cell.style.width = width + 'px';
  cell.style.height = height + 'px';

  return new THREE.CSS3DObject( cell );
}

function addVideoFeed () {
  var videoSource = null
    errBack = function(error) {
      console.log("Video capture error: ", error);
    };

  var getUserMedia = null;

  if (navigator.getUserMedia) {
    getUserMedia = function(a, b, c) {
      navigator.getUserMedia(a, b, c);
    }

  } else if (navigator.webkitGetUserMedia) {
    getUserMedia = function(a, b, c) {
      navigator.webkitGetUserMedia(a, b, c);
    }
  }

  if (typeof MediaStreamTrack !== "undefined") {
    MediaStreamTrack.getSources(function(sourceInfos) {
      var sourceInfo, media;

      // find last video source - might need to add check, last video might not
      // always be what we want?
      for (var i = 0; i < sourceInfos.length; i++) {
        sourceInfo = sourceInfos[i];

        if (sourceInfo.kind === 'video') {
          videoSource = sourceInfo.id;

        } else {
          console.log('Some other kind of source: ', sourceInfo);
        }
      }

      // use sourceId to select either front or back camera
      media = { video: { optional: [{ sourceId: videoSource }] } };

      getUserMedia(media, function(stream) {
        var url = window.URL.createObjectURL(stream);

        var video = document.createElement( 'video' );

        vObj = new THREE.CSS3DObject( video );

        vObj.elementL.src = url;
        vObj.elementR.src = url;

        vObj.position.set(0, 1000, -500);

        // camera.position.set(0,1000,0);

        camera.add(vObj);

      }, errBack);
    });
  }
}

function initGyro () {
  gyro.frequency = 100;

  gyro.startTracking(function(o) {
    if (o.gamma) {

      if (o.gamma > 0 && o.gamma < 45) {
        move.up = true;
        move.down = false;

      } else if (o.gamma < 0 && o.gamma > -45) {
        move.up = false;
        move.down = true;
      }
    }
  });
}

function animate () {
  requestAnimationFrame( animate );

  findFocusedCell();

  controls.update();

  renderer.render( scene, camera );

  if (typeof vObj !== "undefined") {
    if (vObj.elementL.paused) {
      vObj.elementL.play();
    }

    if (vObj.elementR.paused) {
      vObj.elementR.play();
    }

    if (move.up) {
      console.log("move up");
      camera.position.y = 3000;
      vObj.position.y = 0;

    } else if (move.down) {
      console.log("move down");
      camera.position.y = 250;
      vObj.position.y = 1000;
    }
  }
}

init();
