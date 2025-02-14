import * as d3 from 'd3';

// Function to create the scatterplot
export function createScatterplot(container, data, xAccessor, yAccessor, labelAccessor, width, height, colorscheme) {
  // Set margins
  const margin = { top: 20, right: 30, bottom: 40, left: 40 };
  const graphWidth = width - margin.left - margin.right;
  const graphHeight = height - margin.top - margin.bottom;

  // Create an SVG container
  const svg = d3.select(container)
    .attr("width", width)
    .attr("height", height)
    .append("g")
    .attr("transform", `translate(${margin.left},${margin.top})`);

  // Define scales
  const xScale = d3.scaleLinear().range([0, graphWidth]);
  const yScale = d3.scaleLinear().range([graphHeight, 0]);

  // Set the domain for the scales based on data
  xScale.domain([d3.min(data, d => xAccessor(d)), d3.max(data, d => xAccessor(d))]);
  yScale.domain([d3.min(data, d => yAccessor(d)), d3.max(data, d => yAccessor(d))]);

  // Create axes
  const xAxis = d3.axisBottom(xScale);
  const yAxis = d3.axisLeft(yScale);

  svg.append("g")
    .attr("class", "x-axis")
    .attr("transform", `translate(0,${graphHeight})`)
    .call(xAxis);

  svg.append("g")
    .attr("class", "y-axis")
    .call(yAxis);

  // Plot the points (scatterplot)
  svg.selectAll(".dot")
    .data(data)
    .enter().append("circle")
    .attr("class", "dot")
    .attr("cx", d => xScale(xAccessor(d)))
    .attr("cy", d => yScale(yAccessor(d)))
    .attr("r", 5)
    .style("fill", (d, i) => colorscheme(i));
}
