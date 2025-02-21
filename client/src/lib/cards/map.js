import * as d3 from 'd3';

// iewof sellerCount = Inputs.range([1, 41], { step: 1, value: 18, label: "Select Number of Top Sellers" });
// Create the select input for sellers 
viewof sellerSelect = Inputs.select( [ "All Sellers", "Top Sellers", ...topSellers.map((seller) => seller.seller) ], { value: "Top Sellers", label: "Seller Selection" } );

export function createMap(sellerCount, sellerSelect) {

    const geoJSON = d3.json("countries-50m (1).json");

    const animalData = corrected_lat_long_issue.map(row => ({
        id: row.id,
        url: row.url,
        title: row.title,
        domain: row.domain,
        description: row.description,
        price: +row.price,
        currency: row.currency,
        location: row.location_x,
        latitude: +row.latitude,
        longitude: +row.longitude,
        animalName: row.mapped_animal_name_partial_match,
        productBrand: row.product_brand,
        products: row.products_x,
        animalParts: row.mapped_animal_part_exact_match,
        seller: row.seller
    }));

    const filteredAnimalData = animalData.filter(row => 
        row.products && row.animalName && row.seller
    );

    const countryTranslationsMap = new Map([
        ["Vereinigtes Königreich", "United Kingdom"],
        ["Litauen", "Lithuania"],
        ["Australien", "Australia"],
        ["Deutschland", "Germany"],
        ["Frankreich", "France"],
        ["Ägypten", "Egypt"],
        ["Bulgarien", "Bulgaria"],
        ["Schweiz", "Switzerland"],
        ["Italien", "Italy"],
        ["Indonesien", "Indonesia"],
        ["Indien", "India"],
        ["Polen", "Poland"],
        ["Hongkong", "Hong Kong"],
        ["Schweden", "Sweden"],
        ["Vereinigte Arabische Emirate", "United Arab Emirates"],
        ["Südkorea", "South Korea"],
        ["Niederlande", "Netherlands"],
        ["Österreich", "Austria"],
        ["sterreich", "Austria"],  // Duplicate key with different capitalization, will overwrite the previous one
        ["Tunesien", "Tunisia"],
        ["Türkei", "Turkey"],
        ["Marokko", "Morocco"],
        ["Ungarn", "Hungary"],
        ["Estland", "Estonia"],
        ["Trkei", "Turkey"],  // Corrected typo "Trkei" to "Turkey"
        ["Kanada", "Canada"],
        ["Vereinigtes Knigreich", "United Kingdom"],  // Fixed typo in "Vereinigtes Knigreich"
        ["Sdkorea", "South Korea"],  // Corrected typo in "Sdkorea"
        ["gypten", "Egypt"],  // Fixed typo in "gypten"
        ["USA", "United States"],
        ["United States of America", "United States"],
        ["US", "United States"]
    ]);

    const correctedData = filteredAnimalData.map(item => {
        const locationParts = item.location.split(", ");
        let country = locationParts[locationParts.length - 1].trim();
        
        // Translate country names if they are in the dictionary
        if (countryTranslationsMap.has(country)) {
        country = countryTranslationsMap.get(country);
        }
    
        return {
        ...item,
        country
        };
    });

    const sellerCounts = d3.rollup(
        filteredAnimalData,
        ads => ads.length,
        ad => ad.seller
    );

    const sellerArray = Array.from(sellerCounts, ([seller, count]) => ({ seller, count }));

    function tp(sellerArray) {
        let cumulativeSum = 0; // Use let instead of const for cumulativeSum
        const totalAds = d3.sum(sellerArray, d => d.count); // Calculate totalAds within the function
        sellerArray.sort((a, b) => b.count - a.count).forEach(d => {
        cumulativeSum += d.count;
        d.cumulativePercentage = (cumulativeSum / totalAds) * 100;
        });
        return sellerArray; // Return the modified sellerArray
    }

    const sellerArray1 = tp(sellerArray);

    const topSellers = sellerArray1.slice(0, sellerCount);

    {// Set up
    // Exchange rates data
    const exchangeRates = {
        USD: 1,
        EUR: 1.1,
        GBP: 1.3,
        CAD: 0.74,
        CHF: 1.1,
        AUD: 0.7,
        HKD: 0.13,
        SGD: 0.73,
        INR: 0.013
    };
    const geoMargin = { top: 40, right: 300, bottom: 100, left: 100 };
    const geoWidth = 1000 - geoMargin.left - geoMargin.right;
    const geoHeight = 700 - geoMargin.top - geoMargin.bottom;
    
    const geoProjection = d3.geoNaturalEarth1()
        .fitSize([geoWidth, geoHeight], geoJSON);
    
    const geoPath = d3.geoPath().projection(geoProjection);
    
    const svg = d3.create('svg')
        .attr('width', geoWidth + geoMargin.left + geoMargin.right)
        .attr('height', geoHeight + geoMargin.top + geoMargin.bottom);
    
    // Create a group to account for the margins around the map
    const g = svg.append('g')
        .attr('transform', `translate()`);
    
    g.selectAll('path')
        .data(geoJSON.features)
        .join('path')
        .attr('d', geoPath)
        .attr('fill', '#d3d3d3')
        .attr('stroke', 'white');
    
    // Draw the map outline (graticule lines)
    svg.append('path')
        .attr('stroke', '#dcdcdc')  // Light grey for the outline
        .attr('fill', 'none');
    
    // Data processing and identifying top sellers
    const sellerCounts = d3.rollup(
        correctedData,
        ads => ads.length,
        ad => ad.seller
    );
    
    const sellerArray = Array.from(sellerCounts, ([seller, count]) => ({ seller, count }));
    const totalAds = d3.sum(sellerArray, d => d.count);
    let cumulativeSum = 0;
    
    sellerArray.sort((a, b) => b.count - a.count).forEach(d => {
        cumulativeSum += d.count;
        d.cumulativePercentage = (cumulativeSum / totalAds) * 100;
    });
    
    const topSellers = sellerArray.slice(0, sellerCount);
    

    function getFilteredData(filteredAnimalData, sellerFilter, topSellers) {
        const validData = filteredAnimalData;
    
        validData.forEach(d => {
        if (d.location) {
            const locationParts = d.location.split(", ");
            d.country = locationParts[locationParts.length - 1];
            if (d.country === "USA" || d.country === "United States of America") {
            d.country = "United States";
            }
        }
        });
    
        if (sellerFilter === "Top Sellers") {
        let cumulativePercentage = 0;
        const adjustedTopSellers = [];
        for (const seller of topSellers) {
            adjustedTopSellers.push(seller);
            cumulativePercentage = seller.cumulativePercentage;
            if (cumulativePercentage >= sellerFilter) {
            break;
            }
        }
        return validData.filter(d => adjustedTopSellers.some(s => s.seller === d.seller));
        } else if (sellerFilter === "All Sellers") {
        return validData;
        } else {
        return validData.filter(d => d.seller === sellerFilter);
        }
    }


    
    const filteredData = getFilteredData(correctedData, sellerSelect, topSellers);
    
    // Define color scales, excluding gray colors
    const excludedColors = ["#8c8c8c", "#999999", "#a3a3a3", "#bdbdbd", "#cccccc", "#d9d9d9"];
    const combinedSchemes = d3.schemeSet3.concat(d3.schemePaired, d3.schemeTableau10);
    const filteredColors = combinedSchemes.filter(color => !excludedColors.includes(color));
    
    const colorScale = d3.scaleOrdinal()
        .domain([0, topSellers.length])
        .range(filteredColors);

    
    // Map each seller to a color
    const sellerColors = new Map();
    topSellers.forEach((seller, index) => {
        sellerColors.set(seller.seller, colorScale(index));
    });

    // Tooltip setup
    const tooltip = d3.select("body").append("div")
        .attr("class", "tooltip")
        .style("position", "absolute")
        .style("visibility", "hidden")
        .style("background", "rgba(0, 0, 0, 0.7)")
        .style("color", "white")
        .style("padding", "5px")
        .style("border-radius", "4px")
        .style("font-size", "12px");

    // Plot ads from non-top sellers as black circles
    svg.selectAll('.non-top-circle')
        .data(filteredData.filter(d => !topSellers.some(s => s.seller === d.seller))) // Non-top sellers
        .join('circle')
        .attr('class', 'non-top-circle')
        .attr('cx', d => geoProjection([d.longitude, d.latitude])[0]) // Longitude to X
        .attr('cy', d => geoProjection([d.longitude, d.latitude])[1]) // Latitude to Y
        .attr('r', 2) // Radius
        .attr('fill', 'black') // Black for non-top sellers
        .attr('opacity', 0.8) // Slight transparency
        .on("mouseover", function(event, d) {
        const convertedPrice = (d.price * exchangeRates[d.currency]).toFixed(2);
        d3.select(this)
            .attr('fill', 'black')
            .attr('r', 6);
        const sellerAdCount = sellerCounts.get(d.seller); d3.select(this) .attr('fill', 'black') .attr('r', 6);
        
        tooltip.style("visibility", "visible")
            .html(`
            <strong>Seller:</strong> ${d.seller} <br>
            <strong>Quantity of Ads:</strong> ${sellerAdCount} <br>
            <strong>Title:</strong> ${d.title} <br>
            <strong>Location:</strong> ${d.location} <br>
            <strong>Specie:</strong> ${d.animalName} <br>
            <strong>Product:</strong> ${d.products} <br>
            <strong>Price (USD):</strong> ${convertedPrice} <br>
            `);
    
        tooltip.style("left", `${event.pageX + 10}px`)
            .style("top", `${event.pageY - 20}px`);
        })
        .on("click", function(event, d) {
        window.open(d.url, "_blank");
        })
        .on("mouseout", function() {
        d3.select(this)
            .attr('fill', 'black')
            .attr('r', 2);
        
        tooltip.style("visibility", "hidden");
        });
    
    // Plot ads from top sellers with unique colors
    topSellers.forEach((seller, index) => {
        svg.selectAll(`.top-circle-${index}`)
        .data(filteredData.filter(d => d.seller === seller.seller)) // Top sellers
        .join('circle')
        .attr('class', `top-circle-${index}`)
        .attr('cx', d => geoProjection([d.longitude, d.latitude])[0]) // Longitude to X
        .attr('cy', d => geoProjection([d.longitude, d.latitude])[1]) // Latitude to Y
        .attr('r', 4) // Radius
        .attr('fill', sellerColors.get(seller.seller)) // Unique color for each top seller
        .attr('opacity', 0.8) // Slight transparency for better visibility
        .on("mouseover", function(event, d) {
            const convertedPrice = (d.price * exchangeRates[d.currency]).toFixed(2);
            const sellerAdCount = sellerCounts.get(d.seller); d3.select(this) .attr('fill', sellerColors.get(seller.seller)) .attr('r', 6);
            d3.select(this)
            .attr('fill', sellerColors.get(seller.seller))
            .attr('r', 6);

            tooltip.style("visibility", "visible")
            .html(`
                <strong>Seller:</strong> ${d.seller} <br>
                <strong>Quantity of Ads:</strong> ${sellerAdCount} <br>
                <strong>Title:</strong> ${d.title} <br>
                <strong>Location:</strong> ${d.location} <br>
                <strong>Specie:</strong> ${d.animalName} <br>
                <strong>Product:</strong> ${d.products} <br>
                <strong>Price (USD):</strong> ${convertedPrice} <br>
            `);
    
            tooltip.style("left", `${event.pageX + 10}px`)
            .style("top", `${event.pageY - 20}px`);
        })
        .on("click", function(event, d) {
            window.open(d.url, "_blank");
        })
        .on("mouseout", function() {
            d3.select(this)
            .attr('fill', sellerColors.get(seller.seller))
            .attr('r', 4);
            
            tooltip.style("visibility", "hidden");
        });
    });
    
    // Add chart title
    svg.append("text")
        .attr("x", (geoWidth + geoMargin.left) / 2)
        .attr("y", geoMargin.top / 2)
        .attr("text-anchor", "middle")
        .style("font-size", "16px")
        .text(`Worldwide Sellers Distribution`);
        
    // Add legend
    const legend = svg.append("g")
        .attr("transform", `translate(${geoWidth + geoMargin.left},${geoMargin.top})`);
    
    // Legend title
    legend.append("text")
        .attr("x", 0)
        .attr("y", 0)
        .style("font-size", "14px")
        .style("font-weight", "bold")
        .text("Legend");
    
    // Black circle legend for non-top sellers
    legend.append("rect")
        .attr("x", 0)
        .attr("y", 20)
        .attr("width", 18)
        .attr("height", 18)
        .attr("fill", 'black')
        .attr('opacity', 0.8);
    legend.append("text")
        .attr("x", 24)
        .attr("y", 34)
        .style("font-size", "12px")
        .text('Non-top Sellers');
    
        // Function to show tooltip for sellers
    function showSellerTooltip(event, seller) {
        const sellerData = filteredData.filter(d => d.seller === seller.seller);
        const totalAds = sellerData.length;
        
        const speciesCount = d3.rollup(
        sellerData,
        v => v.length,
        d => d.animalName
        );
        const topSpecies = Array.from(speciesCount, ([species, count]) => ({ species, count }))
        .sort((a, b) => b.count - a.count)
        .slice(0, 5)
        .map(s => `${s.species}: ${s.count}`)
        .join("<br>");
        
        const productCount = d3.rollup(
        sellerData,
        v => v.length,
        d => d.products
        );
        const topProducts = Array.from(productCount, ([product, count]) => ({ product, count }))
        .sort((a, b) => b.count - a.count)
        .slice(0, 5)
        .map(p => `${p.product}: ${p.count}`)
        .join("<br>");
    
        const locationCount = d3.rollup(
        sellerData,
        v => v.length,
        d => d.country
        );
        const topLocations = Array.from(locationCount, ([location, count]) => ({ location, count }))
        .filter(l => l.location && l.location.toLowerCase() !== "undefined" && l.location.toLowerCase() !== "none")
        .sort((a, b) => b.count - a.count)
        .slice(0, 5)
        .map(l => `${l.location}: ${l.count}`)
        .join("<br>");
    
        const minPrice = d3.min(sellerData, d => d.price * exchangeRates[d.currency]).toFixed(2);
        const medianPrice = d3.median(sellerData, d => d.price * exchangeRates[d.currency]).toFixed(2);
        const meanPrice = d3.mean(sellerData, d => d.price * exchangeRates[d.currency]).toFixed(2);
        const maxPrice = d3.max(sellerData, d => d.price * exchangeRates[d.currency]).toFixed(2);
    
        tooltip.style("visibility", "visible")
        .html(`
            <strong>Seller:</strong> ${seller.seller} <br>
            <strong>Quantity of Ads:</strong> ${totalAds} <br>
            <strong>Top 5 Species:</strong> <br> ${topSpecies} <br>
            <strong>Top 5 Products:</strong> <br> ${topProducts} <br>
            <strong>Top 5 Locations:</strong> <br> ${topLocations} <br>
            <strong>Min Price (USD):</strong> ${minPrice} <br>
            <strong>Median Price (USD):</strong> ${medianPrice} <br>
            <strong>Mean Price (USD):</strong> ${meanPrice} <br>
            <strong>Max Price (USD):</strong> ${maxPrice} <br>
        `);
        
        tooltip.style("left", `${event.pageX + 10}px`)
        .style("top", `${event.pageY - 20}px`);
    }


    // Legend for top sellers with names
    topSellers.forEach((seller, index) => {
        legend.append("rect")
        .attr("x", 0)
        .attr("y", 44 + index * 24)
        .attr("width", 18)
        .attr("height", 18)
        .attr("fill", sellerColors.get(seller.seller))
        .on("mouseover", function(event) {
            showSellerTooltip(event, seller);
        })
        .on("mouseout", function() {
            tooltip.style("visibility", "hidden");
        })
        .on("click", function() {
            const filteredSellerData = getFilteredData(correctedData, seller.seller, topSellers);
    
            // Clear existing circles
            svg.selectAll('circle').remove();
            
            // Plot ads from selected seller
            svg.selectAll(`.top-circle-${index}`)
            .data(filteredSellerData)
            .join('circle')
            .attr('class', `top-circle-${index}`)
            .attr('cx', d => geoProjection([d.longitude, d.latitude])[0]) // Longitude to X
            .attr('cy', d => geoProjection([d.longitude, d.latitude])[1]) // Latitude to Y
            .attr('r', 4) // Radius
            .attr('fill', sellerColors.get(seller.seller)) // Unique color for each top seller
            .attr('opacity', 0.8) // Slight transparency for better visibility
            .on("mouseover", function(event, d) {
                const convertedPrice = (d.price * exchangeRates[d.currency]).toFixed(2);
                const sellerAdCount = sellerCounts.get(d.seller);
                d3.select(this)
                .attr('fill', 'green')
                .attr('r', 6);
        
                tooltip.style("visibility", "visible")
                .html(`
                    <strong>Seller:</strong> ${d.seller} <br>
                    <strong>Quantity of Ads:</strong> ${sellerAdCount} <br>
                    <strong>Title:</strong> ${d.title} <br>
                    <strong>Specie:</strong> ${d.animalName} <br>
                    <strong>Product:</strong> ${d.products} <br>
                    <strong>Price (USD):</strong> ${convertedPrice} <br>
                `);
        
                tooltip.style("left", `${event.pageX + 10}px`)
                .style("top", `${event.pageY - 20}px`);
            })
            .on("click", function(event, d) {
                window.open(d.url, "_blank");
            })
            .on("mouseout", function() {
                d3.select(this)
                .attr('fill', sellerColors.get(seller.seller))
                .attr('r', 4);
                
                tooltip.style("visibility", "hidden");
            });
        });
    
        legend.append("text")
        .attr("x", 24)
        .attr("y", 58 + index * 24)
        .style("font-size", "12px")
        .text(`${index + 1}${index === 0 ? "st" : index === 1 ? "nd" : index === 2 ? "rd" : "th"}: ${seller.seller}`);
    });
    
    return svg.node();
    }
}