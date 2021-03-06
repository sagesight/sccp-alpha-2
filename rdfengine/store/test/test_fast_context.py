import sys
import os
import unittest

from rdflib import Graph, ConjunctiveGraph, URIRef, BNode, plugin

from store.fast import FastStore
from store.base import BaseStore

class ContextTestCase(unittest.TestCase):
  def setUp(self):
    self.store = FastStore()
    self.graph = ConjunctiveGraph(self.store)
    
    self.michel = URIRef(u'michel')
    self.tarek = URIRef(u'tarek')
    self.bob = URIRef(u'bob')
    self.likes = URIRef(u'likes')
    self.hates = URIRef(u'hates')
    self.pizza = URIRef(u'pizza')
    self.cheese = URIRef(u'cheese')

    self.c1 = URIRef(u'context-1')
    self.c2 = URIRef(u'context-2')

  def addStuff(self):
    tarek = self.tarek
    michel = self.michel
    bob = self.bob
    likes = self.likes
    hates = self.hates
    pizza = self.pizza
    cheese = self.cheese
    c1 = self.c1
    
    graph = Graph(self.graph.store, c1)

    graph.add((tarek, likes, pizza))
    graph.add((tarek, likes, cheese))
    graph.add((michel, likes, pizza))
    graph.add((michel, likes, cheese))
    graph.add((bob, likes, cheese))
    graph.add((bob, hates, pizza))
    graph.add((bob, hates, michel))  # gasp!

  def removeStuff(self):
    tarek = self.tarek
    michel = self.michel
    bob = self.bob
    likes = self.likes
    hates = self.hates
    pizza = self.pizza
    cheese = self.cheese
    c1 = self.c1
    graph = Graph(self.graph.store, c1)

    graph.remove((tarek, likes, pizza))
    graph.remove((tarek, likes, cheese))
    graph.remove((michel, likes, pizza))
    graph.remove((michel, likes, cheese))
    graph.remove((bob, likes, cheese))
    graph.remove((bob, hates, pizza))
    graph.remove((bob, hates, michel))  # gasp!

  def addStuffInMultipleContexts(self):
    c1 = self.c1
    c2 = self.c2
    triple = (self.pizza, self.hates, self.tarek)  # revenge!

    # add to default context
    self.graph.add(triple)

    # add to context 1
    graph = Graph(self.graph.store, c1)
    graph.add(triple)

    # add to context 2
    graph = Graph(self.graph.store, c2)
    graph.add(triple)

  def testConjunction(self):
    self.addStuffInMultipleContexts()
    triple = (self.pizza, self.likes, self.pizza)
    # add to context 1
    contextualizedGraph = Graph(self.graph.store, self.c1)
    contextualizedGraph.add(triple)
    
    print(self.store.statements())
    
    self.assertEqual(len(self.graph), len(contextualizedGraph))

  def testAdd(self):
    self.addStuff()

  def testRemove(self):
    self.addStuff()
    self.removeStuff()

  def testLenInOneContext(self):
    c1 = self.c1
    
    # make sure context is empty
    self.graph.remove_context(self.graph.get_context(c1))
    
    contextualizedGraph = Graph(self.graph.store, c1)
    initialLen = len(self.graph)

    for i in range(0, 10):
      contextualizedGraph.add((BNode(), self.hates, self.hates))

    self.assertEqual(len(contextualizedGraph), initialLen + 10)
    self.assertEqual(len(self.graph.get_context(c1)), initialLen + 10)
    
    self.graph.remove_context(self.graph.get_context(c1))
    
    self.assertEqual(len(self.graph), initialLen)
    self.assertEqual(len(contextualizedGraph), 0)

  def testLenInMultipleContexts(self):
    oldLen = len(self.graph)
    self.addStuffInMultipleContexts()
 
    # addStuffInMultipleContexts is adding the same triple to
    # three different contexts. So it's only + 1
    self.assertEqual(len(self.graph), oldLen + 1)

    graph = Graph(self.graph.store, self.c1)
    self.assertEqual(len(graph), oldLen + 1)
  
  def testRemoveInMultipleContexts(self):
    c1 = self.c1
    c2 = self.c2
    triple = (self.pizza, self.hates, self.tarek)  # revenge!
  
    self.addStuffInMultipleContexts()
 
    # triple should be still in store after removing it from c1 + c2
    self.assertTrue(triple in self.graph)
    
    graph = Graph(self.graph.store, c1)
    graph.remove(triple)
    self.assertTrue(triple in self.graph)
    
    graph = Graph(self.graph.store, c2)
    graph.remove(triple)
    self.assertTrue(triple in self.graph)
    
    # now fully remove
    self.graph.remove(triple)
    self.assertTrue(triple not in self.graph)
 
    # add again and see if remove without context removes all triples!
    self.addStuffInMultipleContexts()
    self.graph.remove(triple)
    self.assertTrue(triple not in self.graph)

  def testContexts(self):
    triple = (self.pizza, self.hates, self.tarek)  # revenge!
  
    self.addStuffInMultipleContexts()
  
    def cid(c):
      return c.identifier

    self.assertTrue(self.c1 in map(cid, self.graph.contexts()))
    self.assertTrue(self.c2 in map(cid, self.graph.contexts()))

    contextList = list(map(cid, list(self.graph.contexts(triple))))
    self.assertTrue(self.c1 in contextList, (self.c1, contextList))
    self.assertTrue(self.c2 in contextList, (self.c2, contextList))

  def testRemoveContext(self):
    c1 = self.c1

    self.addStuffInMultipleContexts()
    self.assertEqual(len(Graph(self.graph.store, c1)), 1)
    self.assertEqual(len(self.graph.get_context(c1)), 1)

    self.graph.remove_context(self.graph.get_context(c1))
    self.assertTrue(self.c1 not in self.graph.contexts())

  def testRemoveAny(self):
    Any = None
    self.addStuffInMultipleContexts()
    self.graph.remove((Any, Any, Any))
    self.assertEqual(len(self.graph), 0)
 
  def testTriples(self):
    tarek = self.tarek
    michel = self.michel
    bob = self.bob
    likes = self.likes
    hates = self.hates
    pizza = self.pizza
    cheese = self.cheese
    c1 = self.c1
    asserte = self.assertEqual
    triples = self.graph.triples
    graph = self.graph
    c1graph = Graph(self.graph.store, c1)
    c1triples = c1graph.triples
    Any = None

    self.addStuff()

    # unbound subjects with context
    asserte(len(list(c1triples((Any, likes, pizza)))), 2)
    asserte(len(list(c1triples((Any, hates, pizza)))), 1)
    asserte(len(list(c1triples((Any, likes, cheese)))), 3)
    asserte(len(list(c1triples((Any, hates, cheese)))), 0)

    # unbound subjects without context, same results!
    asserte(len(list(triples((Any, likes, pizza)))), 2)
    asserte(len(list(triples((Any, hates, pizza)))), 1)
    asserte(len(list(triples((Any, likes, cheese)))), 3)
    asserte(len(list(triples((Any, hates, cheese)))), 0)

    # unbound objects with context
    asserte(len(list(c1triples((michel, likes, Any)))), 2)
    asserte(len(list(c1triples((tarek, likes, Any)))), 2)
    asserte(len(list(c1triples((bob, hates, Any)))), 2)
    asserte(len(list(c1triples((bob, likes, Any)))), 1)

    # unbound objects without context, same results!
    asserte(len(list(triples((michel, likes, Any)))), 2)
    asserte(len(list(triples((tarek, likes, Any)))), 2)
    asserte(len(list(triples((bob, hates, Any)))), 2)
    asserte(len(list(triples((bob, likes, Any)))), 1)

    # unbound predicates with context
    asserte(len(list(c1triples((michel, Any, cheese)))), 1)
    asserte(len(list(c1triples((tarek, Any, cheese)))), 1)
    asserte(len(list(c1triples((bob, Any, pizza)))), 1)
    asserte(len(list(c1triples((bob, Any, michel)))), 1)

    # unbound predicates without context, same results!
    asserte(len(list(triples((michel, Any, cheese)))), 1)
    asserte(len(list(triples((tarek, Any, cheese)))), 1)
    asserte(len(list(triples((bob, Any, pizza)))), 1)
    asserte(len(list(triples((bob, Any, michel)))), 1)

    # unbound subject, objects with context
    asserte(len(list(c1triples((Any, hates, Any)))), 2)
    asserte(len(list(c1triples((Any, likes, Any)))), 5)

    # unbound subject, objects without context, same results!
    asserte(len(list(triples((Any, hates, Any)))), 2)
    asserte(len(list(triples((Any, likes, Any)))), 5)

    # unbound predicates, objects with context
    asserte(len(list(c1triples((michel, Any, Any)))), 2)
    asserte(len(list(c1triples((bob, Any, Any)))), 3)
    asserte(len(list(c1triples((tarek, Any, Any)))), 2)

    # unbound predicates, objects without context, same results!
    asserte(len(list(triples((michel, Any, Any)))), 2)
    asserte(len(list(triples((bob, Any, Any)))), 3)
    asserte(len(list(triples((tarek, Any, Any)))), 2)

    # unbound subjects, predicates with context
    asserte(len(list(c1triples((Any, Any, pizza)))), 3)
    asserte(len(list(c1triples((Any, Any, cheese)))), 3)
    asserte(len(list(c1triples((Any, Any, michel)))), 1)

    # unbound subjects, predicates without context, same results!
    asserte(len(list(triples((Any, Any, pizza)))), 3)
    asserte(len(list(triples((Any, Any, cheese)))), 3)
    asserte(len(list(triples((Any, Any, michel)))), 1)

    # all unbound with context
    asserte(len(list(c1triples((Any, Any, Any)))), 7)
    # all unbound without context, same result!
    asserte(len(list(triples((Any, Any, Any)))), 7)
 
    for c in [graph, self.graph.get_context(c1)]:
      # unbound subjects
      asserte(set(c.subjects(likes, pizza)), set((michel, tarek)))
      asserte(set(c.subjects(hates, pizza)), set((bob,)))
      asserte(set(c.subjects(likes, cheese)), set([tarek, bob, michel]))
      asserte(set(c.subjects(hates, cheese)), set())

      # unbound objects
      asserte(set(c.objects(michel, likes)), set([cheese, pizza]))
      asserte(set(c.objects(tarek, likes)), set([cheese, pizza]))
      asserte(set(c.objects(bob, hates)), set([michel, pizza]))
      asserte(set(c.objects(bob, likes)), set([cheese]))

      # unbound predicates
      asserte(set(c.predicates(michel, cheese)), set([likes]))
      asserte(set(c.predicates(tarek, cheese)), set([likes]))
      asserte(set(c.predicates(bob, pizza)), set([hates]))
      asserte(set(c.predicates(bob, michel)), set([hates]))

      asserte(set(c.subject_objects(hates)), set([(bob, pizza), (bob, michel)]))

      asserte(set(c.subject_objects(likes)),
        set([(tarek, cheese), (michel, cheese), (michel, pizza), (bob, cheese), (tarek, pizza)]))

      asserte(set(c.predicate_objects(michel)), set([(likes, cheese), (likes, pizza)]))
      asserte(set(c.predicate_objects(bob)), set([(likes, cheese), (hates, pizza), (hates, michel)]))
      asserte(set(c.predicate_objects(tarek)), set([(likes, cheese), (likes, pizza)]))

      asserte(set(c.subject_predicates(pizza)), set([(bob, hates), (tarek, likes), (michel, likes)]))
      asserte(set(c.subject_predicates(cheese)), set([(bob, likes), (tarek, likes), (michel, likes)]))
      asserte(set(c.subject_predicates(michel)), set([(bob, hates)]))

      asserte(set(c), set(
          [(bob, hates, michel), (bob, likes, cheese),
           (tarek, likes, pizza), (michel, likes, pizza),
           (michel, likes, cheese), (bob, hates, pizza),
           (tarek, likes, cheese)]))

    # remove stuff and make sure the graph is empty again
    self.removeStuff()
    asserte(len(list(c1triples((Any, Any, Any)))), 0)
    asserte(len(list(triples((Any, Any, Any)))), 0)


if __name__ == '__main__':
    unittest.main()