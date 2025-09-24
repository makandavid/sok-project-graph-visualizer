from rdflib import Graph as RDFGraph, URIRef, Literal, BNode
from rdflib.namespace import RDF, XSD
from api.interfaces.data_source_plugin import DataSourcePlugin
from api.models.graph import Graph
import os, re, urllib.request
from datetime import date, datetime


class RdfDataSourcePlugin(DataSourcePlugin):
    def name(self) -> str:
        return "RDF Data Source Plugin"

    def id(self) -> str:
        return "data_source_rdf"

    def get_supported_extensions(self) -> list[str]:
        return ['.ttl']

    def load_data(self, source: str) -> Graph:
        """High‐level orchestration."""
        rdf = self._load_rdf_graph(source)
        type_map = self._collect_type_map(rdf)
        return self._build_graph(rdf, type_map)

    @staticmethod
    def _load_rdf_graph(source: str) -> RDFGraph:
        """Load a Turtle graph from a file or URL."""
        g = RDFGraph()
        if source.startswith(('http://', 'https://')):
            data = urllib.request.urlopen(source).read()
            g.parse(data=data, format='turtle')
        else:
            if not os.path.exists(source):
                raise FileNotFoundError(f"File not found: {source}")
            g.parse(source, format='turtle')
        return g

    def _collect_type_map(self, rdf: RDFGraph) -> dict[str,str]:
        """
        Scan for `rdf:type` triples and map subject → short type label.
        """
        m = {}
        for s, p, o in rdf.triples((None, RDF.type, None)):
            if isinstance(o, URIRef):
                m[str(s)] = self._short_label(str(o))
        return m

    def _build_graph(self, rdf: RDFGraph, type_map: dict[str,str]) -> Graph:
        """
        Two‐pass build:  
         • ensure each subject/object has a node  
         • attach literals and edges  
        """
        graph = Graph()
        lex2id = {}
        next_node = 1
        next_link = 1

        def make_node(lex: str, term) -> int:
            nonlocal next_node
            if lex in lex2id:
                return lex2id[lex]
            nid = str(next_node); next_node += 1
            kind = "uri" if isinstance(term, URIRef) else "bnode" if isinstance(term, BNode) else "literal"
            attrs = {"original": lex, "type": type_map.get(lex, kind)}
            graph.add_node(nid, attrs)
            lex2id[lex] = nid
            return nid

        for s, p, o in rdf:
            subj_lex = str(s)
            sid = make_node(subj_lex, s)

            if p == RDF.type: # already recorded in attrs via type_map
                continue

            if isinstance(o, Literal):
                key = self._sanitize(self._short_label(str(p)))
                val = self._convert_rdf_literal(o)
                node = next(n for n in graph.nodes if n.id == sid)
                existing = node.attributes.get(key)
                node.attributes[key] = (existing + [val]) if isinstance(existing, list) else ( [existing, val] if existing else val )
                continue

            obj_lex = str(o)
            oid = make_node(obj_lex, o)

            graph.add_link(str(next_link), sid, oid)
            link = graph.links[-1]
            link.attributes = {
                "predicate": self._short_label(str(p)),
                "predicate_uri": str(p),
                "triple": (subj_lex, str(p), obj_lex)
            }
            next_link += 1

        return graph

    @staticmethod
    def _short_label(uri: str) -> str:
        """Strip namespaces to get the local name."""
        return uri.split('#')[-1].split('/')[-1] or uri

    @staticmethod
    def _sanitize(s: str) -> str:
        """Make a CSS/JS‐safe identifier."""
        out = re.sub(r'\W+', '_', s) or 'node'
        return ('n'+out) if out[0].isdigit() else out

    @staticmethod
    def _convert_rdf_literal(literal: Literal):
        """Cast XSD literals to native Python types when possible."""
        data_type = literal.datatype
        try:
            if data_type in {
                XSD.int, XSD.integer, XSD.long,
                XSD.short, XSD.unsignedInt, XSD.unsignedByte
            }:
                return int(literal)
            if data_type in {XSD.decimal, XSD.float, XSD.double}:
                return float(literal)
            if data_type in {XSD.date, XSD.dateTime}:
                py = literal.toPython()
                if isinstance(py, (date, datetime)):
                    return py
        except Exception as e:
            print(e)

        return str(literal)
