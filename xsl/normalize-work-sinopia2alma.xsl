<!-- xslt will normalize the Sinopia Work RDFXML structure to the Alma Work RDFXML structure  -->
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
  <xsl:output method="xml" indent="yes"/>

  <xsl:template match="*[local-name()='hasInstance']">
    <bf:hasInstance rdf:resource="{@rdf:resource}" xmlns:bf="http://id.loc.gov/ontologies/bibframe/" xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"/>
  </xsl:template>

  <xsl:template match="bf:Work" xmlns:bf="http://id.loc.gov/ontologies/bibframe/" xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
    <xsl:text disable-output-escaping="yes">&lt;bf:Work rdf:about="</xsl:text>
    <xsl:value-of select="@rdf:about"/>
    <xsl:text disable-output-escaping="yes">" xmlns:bf="http://id.loc.gov/ontologies/bibframe/"&gt;</xsl:text>
    <xsl:apply-templates select="node()"/>
    <xsl:text disable-output-escaping="yes">&lt;/bf:Work&gt;</xsl:text>
  </xsl:template>

  <xsl:template match="@*|node()">
      <xsl:copy>
        <xsl:apply-templates select="@*|node()"/>
      </xsl:copy>
  </xsl:template>

  <xsl:template match="/*" priority="1">
    <bib>
        <record_format>lcbf_work</record_format>
        <suppress_from_publishing>false</suppress_from_publishing>
        <record>
        <rdf:RDF xmlns:bf="http://id.loc.gov/ontologies/bibframe/" xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#" xmlns:sinopia="http://sinopia.io/vocabulary/" xmlns:bflc="http://id.loc.gov/ontologies/bflc/" xmlns:rdfs="http://www.w3.org/2000/01/rdf-schema#">
          <xsl:apply-templates select="node()"/>
        </rdf:RDF>
      </record>
    </bib>
  </xsl:template>
</xsl:stylesheet>