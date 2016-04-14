//initial page load call
function draw(world,network_data,div_name){
    //page update function called after any changes
  function get_node(){return +d3.select(".handle").select("text").text()}

  var width = 1300,
      height = 600;

  var projection = d3.geo.mercator()
      .center([70, 48])
      .scale(650)
      .rotate([-180,0]);

  var path = d3.geo.path()
      .projection(projection);

  var graticule = d3.geo.graticule();

  var svg = d3.select(div_name).append("svg")
      .attr("width", width)
      .attr("height", height);

  svg.append("path")
      .datum(graticule)
      .attr("class", "graticule")
      .attr("d", path);

    function update(){
      //get updated parameters
      node = get_node()

      d3.selectAll('.connection').remove();
      d3.selectAll('.node').remove();
        //Data Driven SVGs
        //build bubble for each category filtered to selected year and discipline

      var connection = svg.selectAll(".connection")
      .data(network_data['links'])
      //need to index links with latest (ie newest) node index in link
      .enter().append("g")
      .filter(function(d) { return !d.distance <= node; })
      .attr("class","connection")
      .append("line")
      .style("stroke","black")
      .attr("x1", function(d){return projection(d['lon_lat_1'])[0]})
      .attr("y1", function(d){return projection(d['lon_lat_1'])[1]})
      .attr("x2", function(d){return projection(d['lon_lat_2'])[0]})
      .attr("y2", function(d){return projection(d['lon_lat_2'])[1]})

      var node = svg.selectAll(".node")
      .data(network_data['nodes'])
      .enter().append("g")
      .filter(function(d) { return !d.State == "CA"; })
      .attr("class","node")
      .append("circle")
      .attr("cx", function (d) {return projection(d['GPS_lon_lat'])[0]; })
      .attr("cy", function (d) {return projection(d['GPS_lon_lat'])[1]; })
      .attr("r", "2px")
      .attr("fill", "red")   
    }

  //build discipline selection pane
  function draw_world(error, world) {
    if (error) throw error;

    svg.insert("path", ".graticule")
        .datum(topojson.feature(world, world.objects.land))
        .attr("class", "land")
        .attr("d", path);

    svg.insert("path", ".graticule")
        .datum(topojson.mesh(world, world.objects.countries, function(a, b) { return a !== b; }))
        .attr("class", "boundary")
        .attr("d", path);
    }
    //build slider and event handler. Code modified from http://bl.ocks.org/zanarmstrong/ddff7cd0b1220bc68a58

    var slider_width = width-400,
        slider_height = 800
        startingValue = 200000;
    // sets scale for slider
    var x = d3.scale.linear()
        .domain([0, 300000])
        .range([0, slider_width])
        .clamp(true);
    // defines brush
    var brush = d3.svg.brush()
        .x(x)
        .extent([startingValue, startingValue])
        .on("brush", brushed);

    var svg_slider = svg.append("svg")
        .attr("width", width)
        .attr("x",200)
        .attr("y",-slider_height/2+60)
        .append("g")

    svg_slider.append("g")
        .attr("class", "x axis")
        // put in middle of screen
        .attr("transform", "translate(0," + slider_height / 2 + ")")
        .attr("x",18)
        // introduce axis
        .call(d3.svg.axis()
        .scale(x)
        .orient("bottom")
        .tickFormat(function(d) { return d; })
        .tickSize(0)
        .tickPadding(12)
        .tickValues([0, 300000]))
      .select(".domain")
      .select(function() {console.log(this); return this.parentNode.appendChild(this.cloneNode(true));})
        .attr("class", "halo");

    var slider = svg_slider.append("g")
        .attr("class", "slider")
        .call(brush);

    slider.selectAll(".extent,.resize")
        .remove();

    slider.select(".background")
        .attr("height", slider_height);

    var handle = slider.append("g")
        .attr("class", "handle");

    handle.append("path")
        .attr("transform", "translate(0," + slider_height / 2 + ")")
        .attr("d", "M 0 -20 V 20");

    handle.append('text')
      .text(startingValue)
      .attr("transform", "translate(" + (-18) + " ," + (slider_height / 2 ) + ")");

    slider
        .call(brush.event)

    function brushed() {
      var value = brush.extent()[0];
      if (d3.event.sourceEvent) { // not a programmatic event
        handle.select('text');
        value = x.invert(d3.mouse(this)[0]);
        brush.extent([value, value])
      }
      handle.attr("transform", "translate(" + x(value) + ",0)");
      handle.select('text').text(Math.floor(value))
        //run update after user changes slider
      update()
    }

    //load disciplines json data
    draw_world(world)
    //initial draw call on page load
    update()
  };