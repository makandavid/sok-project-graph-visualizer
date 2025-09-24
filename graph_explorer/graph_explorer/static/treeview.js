var initializeTreeview = function(graph) {
    const treeviewElement = document.getElementById("treeview");
    treeviewElement.innerHTML = ""; // clear old tree

    var sources = graph.links.map(link => link.source)
                        .filter((value, index, self) => self.indexOf(value) === index);
    var targets = graph.links.map(link => link.target);
    var roots = sources.filter(x => !targets.includes(x));
    var freeNodes = graph.nodes.filter(x => !targets.includes(x) && !sources.includes(x));

    var trees_list;
    if (roots.length == 0)
        trees_list = graph.links.map(link => link.source)
                            .filter((value, index, self) => self.indexOf(value) === index);
    else
        trees_list = roots;

    addChildren(treeviewElement, trees_list.concat(freeNodes));

    function addChildren(ul, list) {
        list.forEach(child => {
            let li = document.createElement("li");
            li.setAttribute("id", "tree" + child.id);
            let span = document.createElement("span");
            span.setAttribute("class", "arrow");
            span.addEventListener("click", listener);
            span.appendChild(document.createTextNode(child.id));
            li.appendChild(span);
            ul.appendChild(li);
        });
    }

    function updateTree(parent) {
        let children = graph.links.filter(link => "tree" + link.source.id === parent.id).map(link => link.target);
        if (children.length !== 0 || hasAttributes(parent)) {
            let ul = document.createElement("ul");
            ul.setAttribute("class", "nested");
            addChildren(ul, children);
            addAttributes(ul, parent.id.substring(4));
            parent.appendChild(ul);
        }
    }

    function listener() {
        focusNode(this.parentElement.id.substring(4), true)
        if (!this.parentElement.querySelector(".nested"))
            updateTree(this.parentElement);
        if (this.parentElement.querySelector(".nested")) {
            this.parentElement.querySelector(".nested").classList.toggle("active");
            this.classList.toggle("arrow-down");
        } else this.classList.remove("arrow");
    }

    function hasAttributes(parent) {
        let nodeId = parent.id.substring(4);
        let node = graph.nodes.find(n => n.id == nodeId);
        return node && node.attributes && Object.keys(node.attributes).length > 0;
    }

    function addAttributes(ul, nodeId) {
        let node = graph.nodes.find(n => n.id == nodeId);
        if (!node || !node.attributes) return;

        Object.entries(node.attributes).forEach(([key, value]) => {
            let li = document.createElement("li");
            li.setAttribute("class", "attribute");
            li.textContent = key + ": " + value;
            ul.appendChild(li);
        });
    }

    window.TreeView = {
        updateTree,
        graph
    };
}
