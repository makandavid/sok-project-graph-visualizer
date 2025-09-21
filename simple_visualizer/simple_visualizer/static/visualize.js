var colors = d3.scaleOrdinal(d3.schemeCategory10);
var svg = d3.select("svg#mainview");
var svgBirdView = d3.select("svg#birdview");
var width = +svg.node().getBoundingClientRect().width;
var height = +svg.node().getBoundingClientRect().height;

var node, link, mini_node, mini_link;

var viewport = svgBirdView.append("rect")
    .attr("id", "viewport")
    .attr("fill", "none")
    .attr("stroke", "red")
    .attr("stroke-width", 2);

var container = svg.append("g")
    .attr("transform", "translate(0,0)scale(1,1)");

svg.call(d3.zoom()
    .scaleExtent([1, 10])
    .on("zoom", function() {
        container.attr("transform", d3.event.transform)
        updateViewport(d3.event.transform)
    }))

container.append('defs').append('marker')
    .attr('id', 'arrowhead')
    .attr('viewBox', [0, -5, 10, 10])
    .attr('refX', 12)
    .attr('refY', 0)
    .attr('markerWidth', 6)
    .attr('markerHeight', 6)
    .attr('orient', 'auto-start-reverse')
    .append('path')
    .attr('d', 'M0,-5L10,0L0,5')
    .style('fill', '#9ecae1');

var simulation = d3.forceSimulation()
    .force("link", d3.forceLink().id(d => d.id).distance(100).strength(1))
    .force("charge", d3.forceManyBody())
    .force("center", d3.forceCenter(width/2, height/2));

var graph = GRAPH_JSON  

update(graph.links, graph.nodes);
updateViewport(d3.zoomIdentity);


function updateViewport(transform) {
    var mainWidth = width;
    var mainHeight = height;

    var birdWidth = +svgBirdView.attr("width");
    var birdHeight = +svgBirdView.attr("height");
    
    var scaleX = birdWidth / mainWidth;
    var scaleY = birdHeight / mainHeight;
    
    var viewWidth = birdWidth / transform.k;
    var viewHeight = birdHeight / transform.k;

    var viewX = -transform.x * scaleX / transform.k;
    var viewY = -transform.y * scaleY / transform.k;
    
    viewport
        .attr("x", viewX)
        .attr("y", viewY)
        .attr("width", viewWidth)
        .attr("height", viewHeight);
}

function update(links, nodes) {
    link = container.selectAll(".link")
        .data(links)
        .enter()
        .append("line")
        .attr("class", "link")
        .attr("marker-end", "url(#arrowhead)")

    mini_link = svgBirdView.selectAll(".link")
        .data(links)
        .enter()
        .append("line")
        .attr("class", "link")

    node = container.selectAll(".node")
        .data(nodes)
        .enter()
        .append("g")
        .attr("class", "node")
        .attr('id', d => d.id)
        .call(d3.drag().on("start", dragstarted).on("drag", dragged))

    mini_node = svgBirdView.selectAll(".node")
        .data(nodes)
        .enter()
        .append("g")
        .attr("class", "node")
        .attr("id", d => d.id)

    node.append("circle")
        .attr("r", 15)
        .style("fill", "lightblue")
        .style("stroke", "black")

    node.append("text")
        .attr("dy", "0.35em")
        .attr("text-anchor", "middle")
        .text(d => d.id)

    mini_node.append("circle")
        .attr("r", 3)
        .style("fill", (d, i) => colors(i))

    mini_node.append("title")
        .text(d => d.id);

    simulation.nodes(nodes).on("tick", ticked);
    simulation.force("link").links(links);
}

function ticked() {
    link
        .attr("x1", d => d.source.x)
        .attr("y1", d => d.source.y)
        .attr("x2", d => d.target.x)
        .attr("y2", d => d.target.y);
    node
        .attr("transform", d => "translate(" + d.x + ", " + d.y + ")");
    mini_link
        .attr("x1", d => d.source.x/5)
        .attr("y1", d => d.source.y/5)
        .attr("x2", d => d.target.x/5)
        .attr("y2", d => d.target.y/5);
    mini_node
        .attr("transform", d => "translate(" + d.x/5 + ", " + d.y/5 + ")");
}

function dragstarted(d) {
    if (!d3.event.active)
        simulation.alphaTarget(0.3).restart()
    d.fx = d.x;
    d.fy = d.y;
}

function dragged(d) {
    d.fx = d3.event.x;
    d.fy = d3.event.y;
}
