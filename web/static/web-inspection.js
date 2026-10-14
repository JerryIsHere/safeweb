(function (root) {
  "use strict";

  function unwrapRedirectParameters(value) {
    let current = value;
    for (let depth = 0; depth < 5; depth += 1) {
      let parsed;
      try { parsed = new URL(current); } catch { break; }
      const embedded = ["url", "u", "next", "redirect", "target", "continue", "dest", "destination"]
        .map((key) => parsed.searchParams.get(key))
        .find((candidate) => candidate && /^https?:\/\//iu.test(candidate));
      if (!embedded || embedded === current) break;
      current = embedded;
    }
    return current;
  }

  function summarizeDnsReplies(entries) {
    const recordTypes = { A: 1, AAAA: 28, MX: 15, NS: 2, CNAME: 5 };
    const replies = Object.fromEntries(entries);
    const records = {};
    const responseCodes = {};
    Object.entries(recordTypes).forEach(([name, type]) => {
      const reply = replies[name];
      if (!reply) return;
      responseCodes[name] = Number(reply.status);
      records[name] = (reply.answers || [])
        .filter((answer) => answer.type === type)
        .map((answer) => answer.data);
    });
    const codes = Object.values(responseCodes);
    const allLookupsFailed = codes.length === 0;
    const addressCodes = [responseCodes.A, responseCodes.AAAA].filter((code) => code !== undefined);
    const domainExists = allLookupsFailed
      ? null
      : codes.some((code) => code === 0)
        ? true
        : addressCodes.length === 2 && addressCodes.every((code) => code === 3)
          ? false
          : null;
    return {
      records,
      responseCodes,
      status: domainExists === true ? "resolved" : domainExists === false ? "missing" : null,
      domainExists,
      addresses: [...new Set([...(records.A || []), ...(records.AAAA || [])])],
      hasMx: Boolean(records.MX?.length),
      hasNs: Boolean(records.NS?.length),
      hasCname: Boolean(records.CNAME?.length),
      answerCount: Object.values(records).flat().length,
    };
  }

  const api = { summarizeDnsReplies, unwrapRedirectParameters };
  root.SafewebWebInspection = api;
  if (typeof module !== "undefined" && module.exports) module.exports = api;
})(globalThis);
