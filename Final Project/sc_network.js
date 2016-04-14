function draw_network(network_data,world,div_name){

  var network_data = beaker.network_data

  var world = beaker.world_data

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

  svg.insert("path", ".graticule")
      .datum(topojson.feature(world, world.objects.land))
      .attr("class", "land")
      .attr("d", path);

  svg.insert("path", ".graticule")
      .datum(topojson.mesh(world, world.objects.countries, function(a, b) { return a !== b; }))
      .attr("class", "boundary")
      .attr("d", path);

      var connection = svg.selectAll(".connection")
    .data(network_data['links'])
    .enter().append("g")
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
    .attr("class","node")
    .append("circle")
    .attr("cx", function (d) {return projection(d['GPS_lon_lat'])[0]; })
    .attr("cy", function (d) {return projection(d['GPS_lon_lat'])[1]; })
    .attr("r", "2px")
    .attr("fill", "red")
 };