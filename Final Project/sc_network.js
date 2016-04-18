
function draw(world_data,network_data,div_name,highlight_list){

    //page update function called after any changes
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

  d3.select("#nNode")
  .attr("max",network_data["nodes"].length)
  .attr("value",network_data["nodes"].length)
  .on("input", function() {
    update(+this.value);
  });

    function update(input_node){
      input_node = +input_node // convert string input to int for equality evaluations

      d3.select(div_name).selectAll(".connection").remove();

      var connection = svg.selectAll(".connection")
      .data(network_data['links'])
      .enter().append("g")
      .attr("class","connection")
      .filter(function(d) { return +d.second_node <= input_node; })
      .append("line")
      .attr("class","link")
      .style("stroke","black")
      .attr("x1", function(d){return projection(d['lon_lat_1'])[0]})
      .attr("y1", function(d){return projection(d['lon_lat_1'])[1]})
      .attr("x2", function(d){return projection(d['lon_lat_2'])[0]})
      .attr("y2", function(d){return projection(d['lon_lat_2'])[1]})

      // connection.exit().remove();

      d3.select(div_name).selectAll(".node").remove();

      var node = svg.selectAll(".node")
      .data(network_data['nodes'], function(d){ return d.SC_index})
      .enter().append("g")
      .attr("class","node")
      .filter(function(d) { return +d.SC_index <= input_node; })
      .append("circle")
      .attr("class","SC")
      .attr("cx", function (d) {return projection(d['GPS_lon_lat'])[0]; })
      .attr("cy", function (d) {return projection(d['GPS_lon_lat'])[1]; })
      .attr("r", "2px")
      .attr("fill", function(d) {
        if (highlight_list.indexOf(d["geohash"]) == -1){
          return "red";
        } else {
          return "yellow";
        }
      })
      d3.select("#nNode-value").text(input_node);
    }

  //build discipline selection pane
  function draw_world(world) {
    svg.insert("path", ".graticule")
        .datum(topojson.feature(world, world.objects.land))
        .attr("class", "land")
        .attr("d", path);

    svg.insert("path", ".graticule")
        .datum(topojson.mesh(world, world.objects.countries, function(a, b) { return a !== b; }))
        .attr("class", "boundary")
        .attr("d", path);
    }
    draw_world(world_data);
    //initial draw call on page load
    update("280");//hard coded initial node count because it breaks graphic when filtering network not on SC_index order
  };