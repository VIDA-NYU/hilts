import * as d3 from 'd3';

export function createchartSeller(sortedSellers) {

  sortedSellers = sortedSellers.slice(0, 10)

  // Set up chart dimensions and margins
  const margin = { top: 100, right: 150, bottom: 150, left: 300 };

  d3.select("div#barchart").select('svg').remove();

  const svg = d3.select("div#barchart")
    .append("svg")
    .attr("preserveAspectRatio", "xMinYMin meet")
    .attr("viewBox", "0 0 1100 900")
    .classed("svg-content-responsive", true);

  const svgNode = svg.node();
  const width = svgNode.getBoundingClientRect().width;
  const height = svgNode.getBoundingClientRect().height;

  // Set up scales for x and y axes
  const x = d3.scaleBand()
    .domain(sortedSellers.map(d => d.seller))
    .range([0, width])
    .padding(0.1);

  const y = d3.scaleLinear()
    .domain([0, d3.max(sortedSellers, d => d.count)])
    .nice()
    .range([height, 0]);

  // Create the bars
  svg.selectAll(".bar")
    .data(sortedSellers)
    .enter()
    .append("rect")
    .attr("class", "bar")
    .attr("x", d => x(d.seller))
    .attr("y", d => y(d.count))
    .attr("width", x.bandwidth())
    .attr("height", d => height - y(d.count))
    .attr("fill", "#4a90e2");

  // Add x-axis
  svg.append("g")
    .attr("class", "x-axis")
    .attr("transform", "translate(0," + height + ")")
    .call(d3.axisBottom(x))
    // .tickSize([0,0])
    .selectAll("text")
    .style("text-anchor", "end")
    .style("font-size", "16px")
    .attr("transform", "rotate(-65)")

  // Add y-axis
  svg.append("g")
    .attr("class", "y-axis")
    .call(d3.axisLeft(y));

  // Add axis labels
  svg.append("text")
    .attr("x", width / 2)
    .attr("y", height + margin.bottom - 10)
    .style("text-anchor", "middle")
    .text("Sellers");

  // svg.append("text")
  //   .attr("transform", "rotate(-90)")
  //   .attr("x", -height / 2)
  //   .attr("y", -margin.left + 10)
  //   .style("text-anchor", "middle")
  //   .text("Count");

  svg.append("text")
    .attr("x", (width + margin.left - margin.right) / 2)
    .attr("y", (margin.top - margin.bottom))
    .attr("text-anchor", "middle")
    .attr("font-size", "16px")
    .attr("font-weight", "bold")
    .text("Sellers of selected product and Animal");
}
