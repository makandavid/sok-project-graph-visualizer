var sources = graph.links.map(link => link.source)
                        .filter(function (value, index, self) {
                            return self.indexOf(value) === index;
                        });
var targets = graph.links.map(link => link.target);
var roots = sources.filter(x => !targets.includes(x));
var freeNodes = graph.nodes.filter(x => !targets.includes(x) && !sources.includes(x));

if (roots.length == 0)
    trees_list = graph.links.map(link => link.source)
                        .filter(function (value, index, self) {
                            return self.indexOf(value) === index;
                        });
else
    trees_list = roots;

addChildren(document.getElementById("treeview"), trees_list.concat(freeNodes));

function addChildren(ul, list) {
    list.forEach(child => {
        let li = document.createElement("li");
        li.setAttribute("id", "tree"+child.id);
        let span = document.createElement("span");
        span.setAttribute("class", "arrow");
        span.addEventListener("click", listener);
        span.appendChild(document.createTextNode(child.attributes.name?child.attributes.name:child.id));
        li.appendChild(span);
        ul.appendChild(li);
    });
}

function updateTree(parent) {
    children = graph.links.filter(link => "tree"+link.source.id === parent.id).map(link => link.target);
    if (children.length !== 0) {
        let ul = document.createElement("ul");
        ul.setAttribute("class", "nested");
        addChildren(ul, children);
        parent.appendChild(ul);
    }
}

function listener() {
    container.selectAll(".selected").attr("class", "node");
    svgBirdView.selectAll(".selected").attr("class", "node");
    document.getElementById(this.parentElement.id.substring(4)).setAttribute("class", "node selected");
    svgBirdView.select("#mini"+this.parentElement.id.substring(4)).attr("class", "node selected");
    if (!this.parentElement.querySelector(".nested"))
        updateTree(this.parentElement);
    if (this.parentElement.querySelector(".nested")) {
        this.parentElement.querySelector(".nested").classList.toggle("active");
        this.classList.toggle("arrow-down");
    } else this.classList.remove("arrow");
}