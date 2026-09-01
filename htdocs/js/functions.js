      //Create a text canvas
      function createTextCanvas(text, color, font, size) {
        size = size || 24;
        var canvas = document.createElement('canvas');
        var ctx = canvas.getContext('2d');
        var fontStr = (size + 'px ') + (font || 'Arial');
        ctx.font = fontStr;
        var w = ctx.measureText(text).width;
        var h = Math.ceil(size);
        canvas.width = w;
        canvas.height = h;
        ctx.font = fontStr;
        ctx.fillStyle = color || 'black';
        ctx.fillText(text, 0, Math.ceil(size*0.8));
        return canvas;
      }

	  //Create 2D text labels
      function createText2D(text, color, font, size, segW, segH) {
        var canvas = createTextCanvas(text, color, font, size);
        var plane = new THREE.PlaneGeometry(canvas.width, canvas.height, segW, segH);
        var tex = new THREE.Texture(canvas);
        tex.needsUpdate = true;
        var planeMat = new THREE.MeshBasicMaterial({
          map: tex, color: 0xffffff, transparent: true
        });
        var mesh = new THREE.Mesh(plane, planeMat);
        mesh.scale.set(0.25, 0.25, 0.25);
        mesh.doubleSided = true;
        return mesh;
      }
	  
	  	  
	  //Return new vertex from x,y,z coordinates
      function v(x,y,z){ return new THREE.Vertex(new THREE.Vector3(x,y,z)); }

	// Create a line
	function create_line(startCoords, endCoords, color)
	{
    var lineMat = new THREE.LineBasicMaterial( { color: color, opacity: 1, linewidth: 10 } );

    var geom = new THREE.Geometry();
    geom.vertices.push( new THREE.Vertex( new THREE.Vector3(startCoords[0],startCoords[1],startCoords[2]) ) );
    geom.vertices.push( new THREE.Vertex( new THREE.Vector3(endCoords[0], endCoords[1], endCoords[2]) ) );

    line = new THREE.Line(geom, lineMat);
    return line;
	}

	//Create a cylinder
	function create_cylinder(radiusTop,radiusBottom, height, segmentsRadius, segmentsHeight, openEnded, color)
	{
    var material = new THREE.MeshLambertMaterial({
        color: color, //0x0000ff
		opacity: 0.2
    });
    var cylinder = new THREE.Mesh(new THREE.CylinderGeometry(radiusTop,radiusBottom, height, segmentsRadius, segmentsHeight, openEnded), material);
	//( radiusTop <Number>, radiusBottom <Number>, height <Number>, segmentsRadius <Number>, segmentsHeight <Number>, openEnded <Boolean> )
	//segments are how many sections to create the curved surface of the cylinder out of
    cylinder.overdraw = true;
	
    return cylinder;
	}
	
	//Math functions
	function degs2rads(a) {
		return a*(Math.PI/180);
		//radians = degrees * (Math.PI/180)
	}
	function rads2degs(a) {
		return a*(180/Math.PI);
		//degrees = radians * (180/Math.PI)
	}