var HOVER_CLICK_SPEED = 400,
  INPUT_DISTANCE = 500,
  POINTER_Z = -200,
  PAGE_WIDTH = 480,
  WIKI_ROOT = "http://en.wikipedia.org/w/api.php",
  PAGE_CLASS = "page-container";

var scene, camera, renderer, controls, pointer, vObj, elemStartHoverTime,
  currentElem;

var move = {
  up: false,
  down: false
};

var linkTitles = [],
  cells = [],
  pages = [];

function prep () {
  var searchForm = document.getElementById("searchForm"),
    inpSearch = document.getElementById("searchInput"),
    btnSearch = document.getElementById("searchButton");

  // show form
  searchForm.style.display = "block";

  btnSearch.onclick = function () {

    // make sure search term entered
    if ( inpSearch.value.length ) {

      // hide form
      searchForm.style.display = "none";

      // initialize VR
      init( inpSearch.value );

    } else {
      alert( "Please enter search term" );
    }
  }
}

function init ( searchTerm ) {
  var pointerRadius, pointerElem;

  // create scene
  scene = new THREE.Scene();

  // add renderer
  renderer = new THREE.CSS3DStereoRenderer();
  renderer.setSize( viewportWidth, viewportHeight );
  renderer.domElement.style.position = 'absolute';
  document.body.appendChild( renderer.domElement );

  // add lighting
  scene.add( new THREE.AmbientLight( 0x666666 ) );
  light = new THREE.PointLight( 0xaaddaa, .5 );
  light.position.set( 50, 1200, -500 );
  scene.add( light );

  // add camera
  camera = new THREE.PerspectiveCamera( 40, viewportWidth /
      viewportHeight, 1, 1000 );

  scene.add( camera );

  // add view controls
  controls = new THREE.DeviceOrientationControls( camera );

  // calculate pointer size
  pointerRadius = viewportWidth * 0.01 + 'px';

  pointerElem = document.createElement( 'div' );
  pointerElem.className = 'pointer';
  pointerElem.style.width = pointerRadius;
  pointerElem.style.height = pointerRadius;

  pointer = new THREE.CSS3DObject( pointerElem );
  pointer.position.set( 0, 0, POINTER_Z );

  camera.add( pointer );

  // requestPage( searchTerm );

  animate();

  initGyro();

  addVideoFeed();
}

function requestPage ( title ) {
  $.ajax({
      type: "GET",
      url: WIKI_ROOT +
          "?action=parse&format=json&prop=text&section=0&page=" + title +
          "&callback=?",
      contentType: "application/json; charset=utf-8",
      async: false,
      dataType: "json",
      success: makePage,
      error: function (errorMessage) {
        console.log("error: ", errorMessage);
      }
  });
}

// TODO: start using template
function makePage ( data, textStatus, jqXHR ) {
  var pageElem, headerElem, titleElem, closeElem, contentElem, pageObj, pagePos;

  pageElem = document.createElement( 'div' );
  pageElem.className = PAGE_CLASS;
  // pageElem.setAttribute( "data-index", pages.length );

  // make header
  // headerElem = document.createElement( 'header' );
  // headerElem.className = "page-header";

  // make title
  // titleElem = document.createElement( 'span' );
  // titleElem.innerText = data.parse.title;
  // titleElem.className = "page-title";
  // headerElem.appendChild( titleElem );

  // make close button
  // closeElem = document.createElement( 'button' );
  // closeElem.className = "btnClose";
  // closeElem.innerText = "X";
  // headerElem.appendChild( closeElem );

  // pageElem.appendChild( headerElem );

  contentElem = document.createElement( 'div' );
  contentElem.innerHTML = "{{ imgText|Safe }}";
  contentElem.className = "page-content";

  pageElem.appendChild( contentElem );

  pageObj = new THREE.CSS3DObject( pageElem );

  pages.push( pageObj );

  // recalculate page positions
  calculatePagePositions();

  scene.add( pageObj );

  pageObj.lookAt( camera.position );
}

// need to rewrite to handle page removal
function calculatePagePositions () {
  var angle = findAngle( pages.length ),
    distance = ( PAGE_WIDTH / 2 ) / Math.tan( angle / 2 ),
    pageScrollY,
    lastAngle = 90,
    pos;

  if (distance < INPUT_DISTANCE) {
    distance = INPUT_DISTANCE;
  }

  for (var i = pages.length - 1; i >= 0 ; i--) {
    pos = findNextPagePosition( lastAngle, distance );
    lastAngle -= angle;

    pageScrollY = pages[i].position.y

    pages[i].position.set( pos.x, pos.y, pos.z );
    pages[i].lookAt( camera.position );

    // reset y scroll - if done before lookAt(camera.position), page will be tilted
    pages[i].position.y = pageScrollY;
  }
}

function findNextPagePosition ( angle, distance ) {
  return {
    x: camera.position.x + ( distance * Math.cos( angle ) ),
    y: 0,
    z: camera.position.z + ( distance * Math.sin( angle ) )
  };
}

function findAngle ( numItems ) {
  numItems = numItems > 8 ? numItems : 8;

  return ( 2 * Math.PI ) / numItems;
}

function findPointerElem () {
  var p = pointer.elementL.getBoundingClientRect(),
    elem = document.elementFromPoint( p.left, p.top );

  return elem ? elem : false;
}

function trackUIEvents () {
  var elem = findPointerElem(),
    page,
    hoverTime,
    index;

  // element changed
  if (elem !== currentElem) {
    currentElem = elem;

    elemStartHoverTime = new Date();

    // reset pointer to original distance / size
    pointer.position.z = POINTER_Z;

    pointer.elementL.className = "pointer";
    pointer.elementR.className = "pointer";
  }

  hoverTime = new Date() - elemStartHoverTime

  // element is link
  if ( elem.nodeName === "A" ) {
    link_title = elem.title;

    // if element hovered over for half second
    if ( hoverTime > HOVER_CLICK_SPEED ) {

      // turn pointer green
      if ( pointer.elementL.className.indexOf( "active-green" ) === -1 ) {
        pointer.elementL.className += " active-green";
        pointer.elementR.className += " active-green";
      }

      // if link not currently opened
      if ( linkTitles.indexOf( link_title ) < 0 ) {
        requestPage( link_title );
        linkTitles.push( link_title );
      }

    // change size of pointer to reflect time hovered over element
    } else if ( hoverTime > 75 ) {
      pointer.position.z = POINTER_Z - hoverTime / 2;
    }

  } else if ( elem.nodeName === "BUTTON" ) {
    page = findElementPage( elem );

    if ( page ) {

      if ( new Date() - elemStartHoverTime > 500 ) {

        index = page.elementL.getAttribute( "data-index" );

        // remove from scene
        scene.remove( pages[ index ] );

        // remove from page list
        pages.splice( index, 1 );

        // recalculate page index
        for ( var i = 0; i < pages.length; i++ ) {
          pages[i].elementL.setAttribute( "data-index", i );
          pages[i].elementR.setAttribute( "data-index", i );
        }
      }

    } else {
      console.log( elem );
    }

  } else {
    link_title = "";
  }
}

function initGyro () {
  gyro.frequency = 100;

  gyro.startTracking(function(o) {
    if ( o.gamma ) {

      if ( o.gamma > 0 && o.gamma < 60 ) {
        move.up = true;
        move.down = false;

      } else if ( o.gamma < 0 && o.gamma > -60 ) {
        move.up = false;
        move.down = true;

      } else {
        move.up = false;
        move.down = false;
      }
    }
  });
}

function findElementPage ( elem ) {
  var page = false,
    parent = elem.parentElement,
    index;

  while ( parent ) {

    if ( parent.className.indexOf( PAGE_CLASS ) >= 0 ) {
      index = parent.getAttribute( "data-index" );
      page = pages[ index ];
      break;
    }

    parent = parent.parentElement;
  }

  return page;
}

function trackPageMovement () {
  var speed = 3,
    page;

  // find page element
  page = findElementPage( findPointerElem() );

  if ( page ) {

    // scroll down
    if ( move.up ) {
      page.position.y -= speed;

    // scroll up
    } else if ( move.down ) {
      page.position.y += speed;
    }
  }
}

function addVideoFeed () {
  var backgroundImage =
    THREE.ImageUtils.loadTexture("{{ imgUrl }}");

  var backgroundShape = new THREE.SphereGeometry(800, 50, 50);

  var material = new THREE.MeshLambertMaterial({
    color: 0xFFFFFF,
    map: backgroundImage,
    side: THREE.BackSide  // .BackSide is inside sphere .FrontSide .DoubleSide
  });

  var universe = new THREE.Mesh( backgroundShape, material );

  scene.add( universe );
}

function animate () {
  requestAnimationFrame( animate );

  trackUIEvents();

  controls.update();

  renderer.render( scene, camera );

  // if video objects, make sure videos are playing
  if ( typeof vObj !== "undefined" ) {

    if ( vObj.elementL.paused ) {
      vObj.elementL.play();
    }

    if ( vObj.elementR.paused ) {
      vObj.elementR.play();
    }
  }

  trackPageMovement();
}

window.addEventListener( "keydown", function ( event ) {

  // return / enter - hide keyboard
  if ( event.keyCode === 13 ) {
    event.srcElement.blur();
    document.getElementById( "searchButton" ).click();
  }
}, true );

prep();
