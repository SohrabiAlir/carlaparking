

data = [
	(306.9, -172.7),
	(293.5, -172.6),
	(287.7, -187.0),
	(286.6, -198.1),
	(287.1, -211.1),
	(287.2, -235.4),
	(274.3, -240.1),
	(265.6, -223.1),
	(265.9, -204.3),
	(266.2, -186.5),
	(277.5, -179.7),
	(298.1, -180.1),
	(304.6, -201.7),
	(304.1, -219.7),
	(303.9, -235.2),
	(295.7, -239.9),
	(279.9, -250.3),
]

def main():
  
  waypoints = ""
  
  for x, y in data:
    waypoints += """
          <Waypoint routeStrategy="shortest">
            <Position>
              <WorldPosition x=\"""" + str(x) + """"\" y=\"""" + str(y) + """\" />
            </Position>
          </Waypoint>"""
  
  result = """<Action name="AssignPath">
  <PrivateAction>
    <RoutingAction>
      <AssignRouteAction>
        <Route name="example_route" closed="false">\n""" + waypoints + """\n
        </Route>
      </AssignRouteAction>
    </RoutingAction>
  </PrivateAction>
</Action>"""
			  
  print(result)

if __name__ == '__main__':
  main()